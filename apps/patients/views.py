from datetime import datetime, timedelta

from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.contrib.gis.geos import Point
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
                                      IsSelfFamilyMember,
                                      IsSelfAddress, SelfUserAccess)
from utils.custom_sms import send_sms
from utils.utils import manipal_admin_object, patient_user_object

from .emails import (send_email_activation_otp,
                     send_family_member_email_activation_otp)
from .exceptions import (InvalidCredentialsException, InvalidEmailOTPException,
                         InvalidUHID, OTPExpiredException,
                         PatientDoesNotExistsValidationException,
                         PatientMobileDoesNotExistsValidationException,
                         PatientMobileExistsValidationException,
                         PatientOTPExceededLimitException)
from .models import FamilyMember, Patient, PatientAddress
from .serializers import (FamilyMemberSerializer, PatientAddressSerializer,
                          PatientSerializer)
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
    search_fields = ['first_name', 'mobile', 'email']
    ordering_fields = ('-created_at',)

    def get_permissions(self):

        if self.action in ['create', 'verify_login_otp', 'generate_login_otp', ]:
            permission_classes = [AllowAny]
            return [permission() for permission in permission_classes]

        if self.action in ['generate_uhid_otp', 'validate_uhid_otp', \
        'generate_email_verification_otp', 'verify_email_otp']:
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
        random_email_otp = get_random_string(
            length=4, allowed_chars='0123456789')
        otp_expiration_time = datetime.now(
        ) + timedelta(seconds=int(OTP_EXPIRATION_TIME))

        user_obj = serializer.save(
            otp_expiration_time=otp_expiration_time,
            email_otp_expiration_time=otp_expiration_time,
            email_otp=random_email_otp,
            is_active=True)

        user_obj.set_password(random_password)
        user_obj.save()

        send_email_activation_otp(str(user_obj.id), random_email_otp)

        message = "OTP to activate your account is {}, this OTP will expire in {} seconds.".format(
            random_password, OTP_EXPIRATION_TIME)
        if self.request.query_params.get('is_android', True):
            message = '<#> ' + message + ' ' + ANDROID_SMS_RETRIEVER_API_KEY
        is_message_sent = send_sms(mobile_number=str(
            user_obj.mobile.raw_input), message=message)
        if is_message_sent:
            self.create_success_message = 'Your registration is completed successfully. Activate your account by entering the OTP which we have sent to your mobile number.'
        else:
            self.create_success_message = 'Your registration completed successfully, we are unable to send OTP to your number. Please try after sometime.'

    def perform_update(self, serializer):
        is_email_to_be_verified = False
        patient_object = self.get_object()

        if 'email' in serializer.validated_data and \
                not patient_object.email == serializer.validated_data['email']:
            is_email_to_be_verified = True

        if is_email_to_be_verified:
            random_email_otp = get_random_string(
                length=4, allowed_chars='0123456789')
            otp_expiration_time = datetime.now(
            ) + timedelta(seconds=int(OTP_EXPIRATION_TIME))

            send_email_activation_otp(str(patient_object.id), random_email_otp)

            patient_object.email_otp = random_email_otp
            patient_object.email_otp_expiration_time = otp_expiration_time
            patient_object.save()

        patient_object = serializer.save(
            email_verified=not is_email_to_be_verified)

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
    def verify_email_otp(self, request):
        email_otp = request.data.get('email_otp')
        authenticated_patient = patient_user_object(request)

        if not authenticated_patient.email_otp == email_otp:
            raise InvalidEmailOTPException

        if datetime.now().timestamp() > \
                authenticated_patient.email_otp_expiration_time.timestamp():
            raise OTPExpiredException

        random_email_otp = get_random_string(
            length=4, allowed_chars='0123456789')

        authenticated_patient.email_otp = random_email_otp
        authenticated_patient.email_verified = True
        authenticated_patient.save()

        data = {
            "data": None,
            "message": "You email is verified successfully!",
        }
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'])
    def generate_email_verification_otp(self, request):
        authenticated_patient = patient_user_object(request)

        if authenticated_patient.email_verified:
            raise ValidationError("Invalid request!")

        random_email_otp = get_random_string(
            length=4, allowed_chars='0123456789')
        otp_expiration_time = datetime.now(
        ) + timedelta(seconds=int(OTP_EXPIRATION_TIME))

        send_email_activation_otp(
            str(authenticated_patient.id), random_email_otp)

        authenticated_patient.email_otp = random_email_otp
        authenticated_patient.email_otp_expiration_time = otp_expiration_time
        authenticated_patient.save()

        data = {
            "data": {"email": str(authenticated_patient.email), },
            "message": "OTP to verify you email is sent successfully!",
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
            if not request_patient:
                raise PatientMobileDoesNotExistsValidationException

        if facebook_id:
            request_patient = self.get_queryset().filter(
                google_id=facebook_id).first()
        if google_id:
            request_patient = self.get_queryset().filter(
                google_id=google_id).first()

        if not request_patient:
            raise PatientDoesNotExistsValidationException

        random_password = get_random_string(
            length=4, allowed_chars='0123456789')
        otp_expiration_time = datetime.now(
        ) + timedelta(seconds=int(OTP_EXPIRATION_TIME))

        request_patient.otp_expiration_time = otp_expiration_time
        request_patient.set_password(random_password)
        request_patient.save()

        message = "OTP to login into your account is {}, this OTP will expire in {} seconds".format(
            random_password, OTP_EXPIRATION_TIME)
        if not request_patient.is_active:
            message = "OTP to activate your account is {}, this OTP will expire in {} seconds".format(
                random_password, OTP_EXPIRATION_TIME)

        if self.request.query_params.get('is_android', True):
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
        is_capture_details_enabled = request.data.get(
            'is_capture_details_enabled', False)

        if not uhid_number:
            raise ValidationError(
                "Enter valid UHID number.")

        patient_info = patient_user_object(request)
        if patient_info.uhid_number == uhid_number:
            raise ValidationError(
                "This UHID is already linked to your account!")

        if self.model.objects.filter(uhid_number=uhid_number).exists():
            raise ValidationError(
                "There is an exisiting user  on our platform with this UHID.")

        if FamilyMember.objects.filter(patient_info=patient_info,
                                       uhid_number=uhid_number).exists():
            raise ValidationError(
                "You have an existing family member with this UHID.")
        uhid_user_info = fetch_uhid_user_details(request)

        patient_user_obj = self.get_object()

        if is_capture_details_enabled:
            patient_user_obj.email_verified = True
            patient_user_obj.first_name = uhid_user_info['first_name']
            patient_user_obj.last_name = None
            patient_user_obj.middle_name = None
            patient_user_obj.email = uhid_user_info['email']
            patient_user_obj.gender = uhid_user_info['gender']

        patient_user_obj.uhid_number = uhid_number
        patient_user_obj.save()
        data = {
            "data": self.get_serializer(self.get_object()).data,
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
    queryset = FamilyMember.objects.all().order_by('created_at')
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
        if self.action in ['create',]:
            permission_classes = [IsPatientUser]
            return [permission() for permission in permission_classes]

        if self.action in ['partial_update', 'retrieve',
                           'verify_family_member_email_otp',
                           'verify_family_member_otp',
                           'generate_family_member_mobile_verification_otp',
                           'generate_family_member_email_verification_otp']:
            permission_classes = [IsPatientUser & IsSelfFamilyMember]
            return [permission() for permission in permission_classes]

        if self.action == 'list':
            permission_classes = [IsManipalAdminUser | IsPatientUser]
            return [permission() for permission in permission_classes]

        if self.action == 'update':
            permission_classes = [BlacklistUpdateMethodPermission]
            return [permission() for permission in permission_classes]

        return super().get_permissions()

    def get_queryset(self):
        qs = super().get_queryset().filter(patient_info__id=self.request.user.id,
                                           is_visible=True)
        if manipal_admin_object(self.request):
            try:
                request_patient_info = Patient.objects.get(
                    id=self.request.query_params.get('patient_id'))
            except:
                if not request_patient_info:
                    raise ValidationError(
                        "Invalid patient information.")

            qs = FamilyMember.objects.filter(
                patient_info__id=request_patient_info.id, is_visible=True)
        return qs

    def perform_create(self, serializer):
        if not 'email' in serializer.validated_data or \
                not serializer.validated_data['email']:
            raise ValidationError("Email is not mentioned!")

        random_email_otp = get_random_string(
            length=4, allowed_chars='0123456789')
        random_mobile_password = get_random_string(
            length=4, allowed_chars='0123456789')
        otp_expiration_time = datetime.now(
        ) + timedelta(seconds=int(OTP_EXPIRATION_TIME))

        is_mobile_to_be_verified = True
        is_email_to_be_verified = True
        is_visible = False

        request_patient = patient_user_object(self.request)

        if serializer.validated_data['mobile'] == request_patient.mobile:
            is_mobile_to_be_verified = False
            is_visible = True

        if serializer.validated_data['email'] == request_patient.email:
            is_email_to_be_verified = False

        user_obj = serializer.save(
            mobile_otp_expiration_time=otp_expiration_time,
            email_otp_expiration_time=otp_expiration_time,
            mobile_verification_otp=random_mobile_password,
            email_verification_otp=random_email_otp,
            mobile_verified=not is_mobile_to_be_verified,
            email_verified=not is_email_to_be_verified,
            is_visible=is_visible
        )

        self.create_success_message = "Family member is added successfully!"
        
        if is_mobile_to_be_verified:
            message = "You have been added as a family member on Manipal Hospital application by\
            {}, OTP to activate your account is {}, this OTP will expire in {} seconds".format(
                request_patient.first_name,
                random_mobile_password, OTP_EXPIRATION_TIME)

            if self.request.query_params.get('is_android', True):
                message = '<#> ' + message + ' ' + ANDROID_SMS_RETRIEVER_API_KEY
            is_message_sent = send_sms(mobile_number=str(
                user_obj.mobile.raw_input), message=message)
            if is_message_sent:
                self.create_success_message = 'Please enter OTP which we have sent to your family member.'
            else:
                self.create_success_message = 'We are unable to send OTP to your family member. Please try after sometime.'

        if is_email_to_be_verified:
            send_family_member_email_activation_otp(str(user_obj.id), random_email_otp)

    def perform_update(self, serializer):
        request_patient = patient_user_object(self.request)
        family_member_object = self.get_object()
        is_email_to_be_verified = False
        is_mobile_to_be_verified = False

        if 'mobile' in serializer.validated_data and \
                not family_member_object.mobile == serializer.validated_data['mobile'] and \
                not serializer.validated_data['mobile'] == request_patient.mobile:
            is_mobile_to_be_verified = True

        if 'email' in serializer.validated_data and \
                not family_member_object.email == serializer.validated_data['email'] and \
                not serializer.validated_data['email'] == request_patient.email:
            is_email_to_be_verified = True

        if is_email_to_be_verified:
            random_email_otp = get_random_string(
                length=4, allowed_chars='0123456789')
            otp_expiration_time = datetime.now(
            ) + timedelta(seconds=int(OTP_EXPIRATION_TIME))

            family_member_object.email_verification_otp = random_email_otp
            family_member_object.email_otp_expiration_time = otp_expiration_time
            family_member_object.save()

            send_family_member_email_activation_otp(str(family_member_object.id), random_email_otp)

        if is_mobile_to_be_verified:
            random_mobile_password = get_random_string(
                length=4, allowed_chars='0123456789')
            otp_expiration_time = datetime.now(
            ) + timedelta(seconds=int(OTP_EXPIRATION_TIME))

            family_member_object.mobile_verification_otp = random_mobile_password
            family_member_object.mobile_otp_expiration_time = otp_expiration_time
            family_member_object.save()

            message = "Your mobile number has been added on Manipal Hospital application by\
            {}, OTP to activate your account is {}, this OTP will expire in {} seconds".format(
                request_patient.first_name,
                random_mobile_password, OTP_EXPIRATION_TIME)

            if self.request.query_params.get('is_android', True):
                message = '<#> ' + message + ' ' + ANDROID_SMS_RETRIEVER_API_KEY
            is_message_sent = send_sms(mobile_number=str(
                family_member_object.mobile.raw_input), message=message)
            if is_message_sent:
                self.update_success_message = 'Family member details updated successfully, please enter OTP which we have sent to your family member.'
            else:
                self.update_success_message = 'Family member detials updated successfully, we are unable to send OTP to your family member. Please try after sometime.'

        family_member_object = serializer.save(
            mobile_verified=not is_mobile_to_be_verified)

    @action(detail=False, methods=['POST'])
    def validate_new_family_member_uhid_otp(self, request):
        uhid_number = request.data.get('uhid_number')
        if not uhid_number:
            raise ValidationError(
                "Enter valid UHID number.")

        patient_info = patient_user_object(request)
        if patient_info.uhid_number == uhid_number:
            raise ValidationError(
                "Your cannnot associate your UHID number to your family member.")

        if self.model.objects.filter(patient_info=patient_info,
                                     uhid_number=uhid_number).exists():
            raise ValidationError(
                "You have an existing family member with this UHID.")
        uhid_user_info = fetch_uhid_user_details(request)
        uhid_user_info['mobile_verified'] = True
        uhid_user_info['is_visible'] = True
        uhid_user_info['email_verified'] = True
        uhid_user_info['patient_info'] = patient_info

        self.model.objects.create(**uhid_user_info)

        serializer = self.get_serializer(self.get_queryset(), many=True)

        data = {
            "data": serializer.data,
            "message": "New family member is added successfully!"
        }
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['PATCH'])
    def update_family_member_uhid(self, request, pk=None):
        uhid_number = request.data.get('uhid_number')
        is_capture_details_enabled = request.data.get(
            'is_capture_details_enabled', False)

        if not uhid_number:
            raise ValidationError(
                "Enter valid UHID number.")

        patient_info = patient_user_object(request)
        if patient_info.uhid_number == uhid_number:
            raise ValidationError(
                "Your cannnot associate your UHID number to your family member.")

        if self.model.objects.filter(patient_info=patient_info,
                                     uhid_number=uhid_number).exists():
            raise ValidationError(
                "You have an existing family member with this UHID.")

        uhid_user_info = fetch_uhid_user_details(request)

        family_member = self.get_object()

        if is_capture_details_enabled:
            family_member.mobile_verified = True
            family_member.email_verified = True
            family_member.first_name = uhid_user_info['first_name']
            family_member.last_name = None
            family_member.middle_name = None
            family_member.mobile = uhid_user_info['mobile']
            family_member.email = uhid_user_info['email']
            family_member.gender = uhid_user_info['gender']

        family_member.uhid_number = uhid_number
        family_member.save()

        serializer = self.get_serializer(self.get_queryset(), many=True)
        data = {
            "data": serializer.data,
            "message": "Your family member UHID is updated successfully!"
        }
        return Response(data, status=status.HTTP_200_OK)

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
        family_member.is_visible = True
        family_member.save()

        serializer = self.get_serializer(self.get_queryset(), many=True)

        data = {
            "data": serializer.data,
            "message": message,
        }
        return Response(data, status=status.HTTP_200_OK)


    @action(detail=True, methods=['PATCH'])
    def verify_family_member_email_otp(self, request, pk=None):
        email_otp = request.data.get('email_otp')
        if not email_otp:
            raise ValidationError("Enter OTP to verify family member!")
        try:
            family_member = self.get_object() 
        except:
            raise NotFound(detail='Requested information not found!')

        if not family_member.email_verification_otp == email_otp:
            raise ValidationError("Invalid OTP is entered!")

        if datetime.now().timestamp() > \
                family_member.email_otp_expiration_time.timestamp():
            raise OTPExpiredException

        random_email_otp = get_random_string(
            length=4, allowed_chars='0123456789')
        family_member.email_verification_otp = random_email_otp
        family_member.email_verified = True
        family_member.save()

        serializer = self.get_serializer(self.get_queryset(), many=True)

        data = {
            "data": serializer.data,
            "message": "Email is verified successfully!",
        }
        return Response(data, status=status.HTTP_200_OK)



    @action(detail=True, methods=['GET'])
    def generate_family_member_email_verification_otp(self, request, pk=None):
        try:
            family_member_object = self.get_object()
        except:
            raise NotFound(detail='Requested information not found!')

        if family_member_object.email_verified:
            raise ValidationError("Invalid request!")

        random_email_otp = get_random_string(
            length=4, allowed_chars='0123456789')
        otp_expiration_time = datetime.now(
        ) + timedelta(seconds=int(OTP_EXPIRATION_TIME))

        send_family_member_email_activation_otp(str(family_member_object.id), random_email_otp)

        family_member_object.email_verification_otp = random_email_otp
        family_member_object.email_otp_expiration_time = otp_expiration_time
        family_member_object.save()

        data = {
            "data": {"email": str(family_member_object.email)},
            "message": "Please enter OTP which we have sent on your email to activate.",
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
            {}, OTP to activate your account is {}, this OTP will expire in {} seconds".format(
            request_patient.first_name,
            random_password, OTP_EXPIRATION_TIME)

        if self.request.query_params.get('is_android', True):
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


class PatientAddressViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsPatientUser]
    model = PatientAddress
    queryset = PatientAddress.objects.all()
    serializer_class = PatientAddressSerializer
    create_success_message = "New address is added successfully."
    list_success_message = 'Addresses returned successfully!'
    retrieve_success_message = 'Address information returned successfully!'
    update_success_message = 'Information is updated successfuly!'
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    search_fields = ['code', 'description', ]
    ordering_fields = ('code',)

    def get_permissions(self):
        if self.action in ['list', 'create', ]:
            permission_classes = [IsPatientUser]
            return [permission() for permission in permission_classes]

        if self.action in ['partial_update', 'retrieve', ]:
            permission_classes = [IsSelfAddress]
            return [permission() for permission in permission_classes]

        if self.action == 'update':
            permission_classes = [BlacklistUpdateMethodPermission]
            return [permission() for permission in permission_classes]

        if self.action == 'destroy':
            permission_classes = [BlacklistDestroyMethodPermission]
            return [permission() for permission in permission_classes]

        return super().get_permissions()

    def get_queryset(self):
        return super().get_queryset().filter(patient_info__id=self.request.user.id)

    def perform_create(self, serializer):
        request_data = self.request.data
        longitude = float(request_data.get("longitude", 0))
        latitude = float(request_data.get("latitude", 0))
        if not (longitude and latitude):
            raise ValidationError(
                "Missing information about longitude and latitude!")
        serializer.save(location=Point(longitude, latitude, srid=4326))

    def perform_update(self, serializer):
        request_data = self.request.data
        longitude = float(request_data.get("longitude", 0))
        latitude = float(request_data.get("latitude", 0))
        if longitude and latitude:
            serializer.save(location=Point(longitude, latitude, srid=4326))
            return

        serializer.save()
