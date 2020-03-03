from datetime import datetime, timedelta

from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.shortcuts import render
from django.utils.crypto import get_random_string
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ParseError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.test import APIRequestFactory
from rest_framework_jwt.utils import jwt_encode_handler, jwt_payload_handler

from apps.master_data.views import ValidateUHIDView
from manipal_api.settings import (ANDROID_SMS_RETRIEVER_API_KEY, JWT_AUTH,
                                  OTP_EXPIRATION_TIME)
from utils import custom_viewsets
from utils.custom_permissions import (BlacklistDestroyMethodPermission,
                                      BlacklistUpdateMethodPermission,
                                      IsManipalAdminUser, IsPatientUser,
                                      SelfUserAccess)
from utils.custom_sms import send_sms
from utils.utils import manipal_admin_object, patient_user_object

from .exceptions import (InvalidCredentialsException, InvalidUHID,
                         OTPExpiredException,
                         PatientDoesNotExistsValidationException,
                         PatientMobileExistsValidationException,
                         PatientOTPExceededLimitException)
from .models import FamilyMember, Patient
from .serializers import FamilyMemberSerializer, PatientSerializer
from .utils import fetch_uhid_user_details


class PatientViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    model = Patient
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    create_success_message = 'Your registration completed successfully!'
    list_success_message = 'Patients list returned successfully!'
    retrieve_success_message = 'Information returned successfully!'
    update_success_message = 'Information updated successfully!'

    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    search_fields = ['first_name', ]
    ordering_fields = ('-created_at',)

    def get_permissions(self):

        if self.action in ['create', 'verify_login_otp', 'generate_login_otp', ]:
            permission_classes = [AllowAny]
            return [permission() for permission in permission_classes]

        if self.action in ['generate_uhid_otp', 'validate_uhid_otp']:
            permission_classes = [IsPatientUser]
            return [permission() for permission in permission_classes]

        if self.action == 'list':
            permission_classes = [IsManipalAdminUser]
            return [permission() for permission in permission_classes]

        if self.action == 'retrieve':
            permission_classes = [SelfUserAccess]
            return [permission() for permission in permission_classes]

        if self.action == 'partial_update':
            permission_classes = [SelfUserAccess]
            return [permission() for permission in permission_classes]

        if self.action == 'update':
            permission_classes = [BlacklistUpdateMethodPermission]
            return [permission() for permission in permission_classes]

        if self.action == 'destroy':
            permission_classes = [BlacklistDestroyMethodPermission]
            return [permission() for permission in permission_classes]

        return super().get_permissions()

    def perform_create(self, serializer):
        if self.get_queryset().filter(mobile=self.request.data.get('mobile')).exists():
            raise PatientMobileExistsValidationException
        random_password = get_random_string(
            length=4, allowed_chars='0123456789')
        otp_expiration_time = datetime.now(
        ) + timedelta(seconds=int(OTP_EXPIRATION_TIME))

        user_obj = serializer.save(
            otp_expiration_time=otp_expiration_time)
        user_obj.set_password(random_password)
        user_obj.save()
        message = "OTP to activate your account is {}, this OTP will expire in {} seconds.".format(
            random_password, OTP_EXPIRATION_TIME)
        if self.request.query_params.get('is_android'):
            message = '<#> ' + message + ' ' + ANDROID_SMS_RETRIEVER_API_KEY
        is_message_sent = send_sms(mobile_number=str(
            user_obj.mobile.raw_input), message=message)
        if is_message_sent:
            self.create_success_message = 'Your registration is completed successfully, please enter OTP which we have sent to activate your account.'
        else:
            self.create_success_message = 'Your registration completed successfully, we are unable to send OTP to your number. Please try after sometime.'

    @action(detail=False, methods=['POST'])
    def verify_login_otp(self, request):
        username = request.data.get('mobile')
        password = request.data.get('password')

        if not (username and password):
            raise InvalidCredentialsException

        authenticated_patient = authenticate(username=username,
                                             password=password)
        if not authenticated_patient:
            raise InvalidCredentialsException
        if datetime.now().timestamp() > \
                authenticated_patient.otp_expiration_time.timestamp():
            raise OTPExpiredException
        message = "Login successful!"

        update_last_login(None, authenticated_patient)
        if not authenticated_patient.is_active:
            authenticated_patient.is_active = True
            message = "Your account is activated successfully!"
        random_password = get_random_string(
            length=4, allowed_chars='0123456789')
        authenticated_patient.set_password(random_password)
        authenticated_patient.save()
        serializer = self.get_serializer(authenticated_patient)

        payload = jwt_payload_handler(authenticated_patient)
        payload['username'] = payload['username'].raw_input
        payload['mobile'] = payload['mobile'].raw_input
        token = jwt_encode_handler(payload)
        expiration = datetime.utcnow(
        ) + JWT_AUTH['JWT_EXPIRATION_DELTA']
        expiration_epoch = expiration.timestamp()

        data = {
            "data": serializer.data,
            "message": message,
            "token": token,
            "token_expiration": expiration_epoch
        }
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'])
    def generate_login_otp(self, request):
        mobile = request.data.get('mobile')
        facebook_id = request.data.get('facebook_id')
        google_id = request.data.get('google_id')

        if not (mobile or facebook_id or google_id):
            raise PatientDoesNotExistsValidationException

        if mobile:
            request_patient = self.get_queryset().filter(
                mobile=mobile).first()
        if facebook_id:
            request_patient = self.get_queryset().filter(
                google_id=facebook_id).first()
        if google_id:
            request_patient = self.get_queryset().filter(
                google_id=google_id).first()

        if not request_patient:
            raise PatientDoesNotExistsValidationException

        # if datetime.now().timestamp() < \
        #         request_patient.otp_expiration_time.timestamp():
        #     raise PatientOTPExceededLimitException

        random_password = get_random_string(
            length=4, allowed_chars='0123456789')
        otp_expiration_time = datetime.now(
        ) + timedelta(seconds=int(OTP_EXPIRATION_TIME))

        request_patient.otp_expiration_time = otp_expiration_time
        request_patient.set_password(random_password)
        request_patient.save()

        message = "OTP to login into your accout is {}, this OTP will expire in {} seconds".format(
            random_password, OTP_EXPIRATION_TIME)
        if not request_patient.is_active:
            message = "OTP to activate your accout is {}, this OTP will expire in {} seconds".format(
                random_password, OTP_EXPIRATION_TIME)

        if self.request.query_params.get('is_android'):
            message = '<#> ' + message + ' ' + ANDROID_SMS_RETRIEVER_API_KEY
        is_message_sent = send_sms(mobile_number=str(
            request_patient.mobile.raw_input), message=message)

        if is_message_sent:
            response_message = 'Please enter OTP which we have sent to login into your account.'
            if not request_patient.is_active:
                response_message = 'Please enter OTP which we have sent to activate your account.'
        else:
            response_message = 'We are unable to send OTP to your number, please try again after sometime.'

        data = {
            "data": {"mobile": str(request_patient.mobile.raw_input), },
            "message": response_message,
        }
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['PATCH'])
    def update_uhid(self, request, pk=None):
        uhid_number = request.data.get('uhid_number')
        uhid_user_info = fetch_uhid_user_details(request)

        patient_info = patient_user_object(request)
        if patient_info.uhid_number == uhid_number:
            raise ValidationError("Invalid request!")

        if self.model.objects.filter(uhid_number=uhid_number).exists():
            raise ValidationError(
                "There is an exisiting user  on our platform with this UHID.")

        if FamilyMember.objects.filter(patient_info=patient_info,
                                       uhid_number=uhid_number).exists():
            raise ValidationError(
                "You have an existing family member with this UHID.")

        patient_user_obj = self.get_object()
        patient_user_obj.uhid_number = uhid_number
        patient_user_obj.save()

        data = {
            "data": uhid_user_info,
            "message": "Your UHID is updated successfully!"
        }
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['POST'])
    def generate_uhid_otp(self, request):
        uhid_number = request.data.get('uhid_number')
        if not uhid_number:
            raise ValidationError('UHID is missing!')

        factory = APIRequestFactory()
        proxy_request = factory.post('', {"uhid": uhid_number}, format='json')
        response = ValidateUHIDView().as_view()(proxy_request)

        if not (response.status_code == 200 and response.data['success']):
            raise ValidationError(response.data['message'])

        data = {
            "data": None,
            "message": response.data['message'],
        }
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'])
    def validate_uhid_otp(self, request):
        uhid_user_info = fetch_uhid_user_details(request)
        data = {
            "data": uhid_user_info,
            "message": "Fetched user details!"
        }
        return Response(data, status=status.HTTP_200_OK)


class FamilyMemberViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    model = FamilyMember
    queryset = FamilyMember.objects.all()
    serializer_class = FamilyMemberSerializer
    create_success_message = 'Your family member has been added successfully!'
    list_success_message = 'Family members list returned successfully!'
    retrieve_success_message = 'Information returned successfully!'
    update_success_message = 'Information updated successfully!'
    delete_success_message = 'Your family member account is deleted successfully!'

    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    search_fields = ['first_name', ]
    ordering_fields = ('-created_at',)

    def get_permissions(self):
        if self.action in ['create', 'generate_family_member_uhid_otp',
                           'validate_family_member_uhid_otp',
                           'generate_family_member_mobile_verification_otp']:
            permission_classes = [IsPatientUser]
            return [permission() for permission in permission_classes]

        if self.action == 'list':
            permission_classes = [IsManipalAdminUser | IsPatientUser]
            return [permission() for permission in permission_classes]

        if self.action == 'partial_update':
            permission_classes = [IsPatientUser]
            return [permission() for permission in permission_classes]

        if self.action == 'update':
            permission_classes = [BlacklistUpdateMethodPermission]
            return [permission() for permission in permission_classes]

        return super().get_permissions()

    def get_queryset(self):
        qs = FamilyMember.objects.filter(patient_info__id=self.request.user.id,
                                         mobile_verified=True)
        if manipal_admin_object(self.request):
            try:
                request_patient_info = Patient.objects.get(
                    id=self.request.query_params.get('patient_id'))
            except:
                if not request_patient_info:
                    raise ValidationError(
                        "Invalid patient information.")

            qs = FamilyMember.objects.filter(
                patient_info__id=request_patient_info.id, mobile_verified=True)
        return qs

    def perform_create(self, serializer):

        random_email_password = get_random_string(
            length=4, allowed_chars='0123456789')
        random_mobile_password = get_random_string(
            length=4, allowed_chars='0123456789')
        otp_expiration_time = datetime.now(
        ) + timedelta(seconds=int(OTP_EXPIRATION_TIME))

        is_mobile_to_be_verified = True
        request_patient = patient_user_object(self.request)

        if serializer.validated_data['mobile'] == request_patient.mobile:
            is_mobile_to_be_verified = False

        user_obj = serializer.save(
            mobile_otp_expiration_time=otp_expiration_time,
            email_otp_expiration_time=otp_expiration_time,
            mobile_verification_otp=random_mobile_password,
            email_verification_otp=random_email_password,
            mobile_verified=not is_mobile_to_be_verified
        )

        self.create_success_message = "Family member is added successfully!"

        if is_mobile_to_be_verified:
            message = "You have been added as a family member on Manipal Hospital application by\
            {}, OTP to activate your accout is {}, this OTP will expire in {} seconds".format(
                request_patient.first_name,
                random_mobile_password, OTP_EXPIRATION_TIME)

            if self.request.query_params.get('is_android'):
                message = '<#> ' + message + ' ' + ANDROID_SMS_RETRIEVER_API_KEY
            is_message_sent = send_sms(mobile_number=str(
                user_obj.mobile.raw_input), message=message)
            if is_message_sent:
                self.create_success_message = 'Please enter OTP which we have sent to your family member.'
            else:
                self.create_success_message = 'We are unable to send OTP to your family member. Please try after sometime.'

    def perform_update(self, serializer):
        request_patient = patient_user_object(self.request)
        is_mobile_to_be_verified = False

        if 'mobile' in serializer.validated_data and \
                not self.get_object().mobile == serializer.validated_data['mobile'] and \
                not serializer.validated_data['mobile'] == request_patient.mobile:
            is_mobile_to_be_verified = True

        family_member_object = serializer.save(
            mobile_verified=not is_mobile_to_be_verified)

        if is_mobile_to_be_verified:
            random_mobile_password = get_random_string(
                length=4, allowed_chars='0123456789')
            otp_expiration_time = datetime.now(
            ) + timedelta(seconds=int(OTP_EXPIRATION_TIME))

            family_member_object.mobile_verification_otp = random_mobile_password,
            family_member_object.mobile_otp_expiration_time = otp_expiration_time,
            family_member_object.save()

            message = "Your mobile number has been added on Manipal Hospital application by\
            {}, OTP to activate your accout is {}, this OTP will expire in {} seconds".format(
                request_patient.first_name,
                random_mobile_password, OTP_EXPIRATION_TIME)

            if self.request.query_params.get('is_android'):
                message = '<#> ' + message + ' ' + ANDROID_SMS_RETRIEVER_API_KEY
            is_message_sent = send_sms(mobile_number=str(
                family_member_object.mobile.raw_input), message=message)
            if is_message_sent:
                self.update_success_message = 'Family member details updated successfully, please enter OTP which we have sent to your family member.'
            else:
                self.update_success_message = 'Family member detials updated successfully, we are unable to send OTP to your family member. Please try after sometime.'

    @action(detail=False, methods=['POST'])
    def validate_new_family_member_uhid_otp(self, request):
        uhid_number = request.data.get('uhid_number')
        uhid_user_info = fetch_uhid_user_details(request)
        uhid_user_info['mobile_verified'] = True
        patient_info = patient_user_object(request)
        if self.model.objects.filter(patient_info=patient_info,
                                     uhid_number=uhid_number).exists():
            raise ValidationError(
                "You have an existing family member with this UHID.")

        uhid_user_info['patient_info'] = patient_info
        family_member_obj = self.model.objects.create(**uhid_user_info)
        # serializer = self.get_serializer(family_member_obj)
        serializer = self.get_serializer(self.get_queryset(), many=True)

        data = {
            "data": serializer.data,
            "message": "New family member is added successfully!"
        }
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['PATCH'])
    def update_family_member_uhid(self, request, pk=None):
        uhid_number = request.data.get('uhid_number')
        uhid_user_info = fetch_uhid_user_details(request)

        patient_info = patient_user_object(request)
        if self.model.objects.filter(patient_info=patient_info,
                                     uhid_number=uhid_number).exists():
            raise ValidationError(
                "You have an existing family member with this UHID.")

        family_member = self.get_object()
        family_member.uhid_number = uhid_number
        family_member.save()

        data = {
            "data": uhid_user_info,
            "message": "Your family member UHID is updated successfully!"
        }
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['PATCH'])
    def verify_family_member_otp(self, request, pk=None):
        mobile_otp = request.data.get('mobile_otp')
        if not mobile_otp:
            raise ValidationError("Enter OTP to verify family member!")
        try:
            # TODO: self.get_object() doesn't seem to work
            family_member = self.model.objects.get(pk=pk)
        except:
            raise NotFound(detail='Requested information not found!')

        if not family_member.mobile_verification_otp == mobile_otp:
            raise ValidationError("Invalid OTP is entered!")

        if datetime.now().timestamp() > \
                family_member.mobile_otp_expiration_time.timestamp():
            raise OTPExpiredException

        message = "Family member is added successfully!"

        random_password = get_random_string(
            length=4, allowed_chars='0123456789')
        family_member.mobile_verification_otp = random_password
        family_member.mobile_verified = True
        family_member.save()

        serializer = self.get_serializer(self.get_queryset(), many=True)

        data = {
            "data": serializer.data,
            "message": message,
        }
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'])
    def generate_family_member_mobile_verification_otp(self, request, pk=None):
        try:
            # TODO: self.get_object() doesn't seem to work
            family_member = self.model.objects.get(pk=pk)
        except:
            raise NotFound(detail='Requested information not found!')

        if family_member.mobile_verified:
            raise ValidationError("Invalid request!")

        random_password = get_random_string(
            length=4, allowed_chars='0123456789')
        otp_expiration_time = datetime.now(
        ) + timedelta(seconds=int(OTP_EXPIRATION_TIME))

        family_member.mobile_verification_otp = random_password
        family_member.mobile_otp_expiration_time = otp_expiration_time
        family_member.save()

        request_patient = patient_user_object(self.request)

        message = "You have been added as a family member on Manipal Hospital application by\
            {}, OTP to activate your accout is {}, this OTP will expire in {} seconds".format(
            request_patient.first_name,
            random_password, OTP_EXPIRATION_TIME)

        if self.request.query_params.get('is_android'):
            message = '<#> ' + message + ' ' + ANDROID_SMS_RETRIEVER_API_KEY
        is_message_sent = send_sms(mobile_number=str(
            family_member.mobile.raw_input), message=message)
        if is_message_sent:
            response_message = 'Please enter OTP which we have sent to your family member.'
        else:
            response_message = 'We are unable to send OTP to your family member. Please try after sometime.'

        data = {
            "data": {"mobile": str(family_member.mobile.raw_input), },
            "message": response_message,
        }
        return Response(data, status=status.HTTP_200_OK)
