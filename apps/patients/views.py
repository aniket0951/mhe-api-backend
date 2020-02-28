from datetime import datetime, timedelta

from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.shortcuts import render
from django.utils.crypto import get_random_string
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.test import APIRequestFactory
from rest_framework_jwt.utils import jwt_encode_handler, jwt_payload_handler

from apps.master_data.views import ValidateUHIDView, ValidateOTPView
from manipal_api.settings import JWT_AUTH, OTP_EXPIRATION_TIME
from utils import custom_viewsets
from utils.custom_permissions import (BlacklistUpdateMethodPermission,
                                      IsManipalAdminUser, IsPatientUser,
                                      SelfUserAccess)
from utils.custom_sms import send_sms
from utils.utils import patient_user_object

from .exceptions import (InvalidUHID, PatientDoesNotExistsValidationException,
                         InvalidCredentialsException,
                         PatientMobileExistsValidationException,
                         PatientOTPExceededLimitException,
                         PatientOTPExpiredException)
from .models import FamilyMember, Patient, PatientUHID
from .serializers import FamilyMemberSerializer, PatientSerializer


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

        if self.action == 'list':
            permission_classes = [IsManipalAdminUser]
            return [permission() for permission in permission_classes]

        if self.action == 'retrieve':
            permission_classes = [SelfUserAccess]
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
            otp_expiration_time=otp_expiration_time, is_primary_account=True)
        user_obj.set_password(random_password)
        user_obj.save()
        message = "OTP to activate your accout is {}, this OTP will expire in {} seconds".format(
            random_password, OTP_EXPIRATION_TIME)
        is_message_sent = send_sms(mobile_number=str(
            user_obj.mobile.raw_input), message=message)
        if is_message_sent:
            self.create_success_message = 'Your registration is completed successfully, please enter OTP which we have sent to activate your account.'
        else:
            self.create_success_message = 'Your registration completed successfully, we are unable to send OTP to your number. Please try after sometime.'

    @action(detail=False, methods=['POST'])
    def verify_login_otp(self, request):
        username = request.data.get('mobile'),
        password = request.data.get('password')
        if not (username and password):
            raise InvalidCredentialsException

        authenticated_patient = authenticate(username=username,
                                             password=password)
        if not authenticated_patient:
            raise InvalidCredentialsException
        if datetime.now().timestamp() > \
                authenticated_patient.otp_expiration_time.timestamp():
            raise PatientOTPExpiredException
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
        uhid_number = request.data.get('uhid_number')
        otp = str(request.data.get('otp'))
        if not (uhid_number and otp):
            raise ValidationError('UHID or OTP is missing!')

        factory = APIRequestFactory()
        proxy_request = factory.post(
            '', {"uhid": uhid_number, "otp": otp}, format='json')
        response = ValidateOTPView().as_view()(proxy_request)

        if not (response.status_code == 200 and response.data['success']):
            raise ValidationError(response.data['message'])

        sorted_keys = ['age', 'DOB', 'email', 'HospNo',
                       'mobile', 'first_name', 'gender', 'Status']
        uhid_user_info = {}
        for index, key in enumerate(sorted(response.data['data'].keys())):
            if key in ['Age', 'DOB', 'HospNo', 'Status']:
                continue
            if not response.data['data'][key]:
                uhid_user_info[key] = None

            uhid_user_info[sorted_keys[index]] = response.data['data'][key]
            
        uhid_user_info['uhid_number'] = uhid_number
        uhid_user_info['raw_info_from_manipal_API'] = response.data['data']

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

    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    search_fields = ['first_name', ]
    ordering_fields = ('-created_at',)

    def get_permissions(self):
        if self.action in ['create', 'generate_family_member_uhid_otp',
                           'validate_family_member_uhid_otp']:
            permission_classes = [IsPatientUser]
            return [permission() for permission in permission_classes]

        if self.action == 'list':
            permission_classes = [IsManipalAdminUser | IsPatientUser]
            return [permission() for permission in permission_classes]

        if self.action == 'retrieve':
            permission_classes = [SelfUserAccess]
            return [permission() for permission in permission_classes]

        return super().get_permissions()

    def get_queryset(self):
        return FamilyMember.objects.filter(patient_info__id=self.request.user.id)

    @action(detail=False, methods=['POST'])
    def validate_new_family_member_uhid_otp(self, request):
        uhid_number = request.data.get('uhid_number')
        otp = str(request.data.get('otp'))
        if not (uhid_number and otp):
            raise ValidationError('UHID or OTP is missing!')

        patient_info = patient_user_object(request)
        if self.model.objects.filter(patient_info=patient_info,
                                     uhid_number=uhid_number).exists():
            raise ValidationError(
                "You have an existing family member with this UHID.")

        factory = APIRequestFactory()
        proxy_request = factory.post(
            '', {"uhid": uhid_number, "otp": otp}, format='json')
        response = ValidateOTPView().as_view()(proxy_request)

        if not (response.status_code == 200 and response.data['success']):
            raise ValidationError(response.data['message'])

        sorted_keys = ['age', 'DOB', 'email', 'HospNo',
                       'mobile', 'first_name', 'gender', 'Status']
        family_member_info = {}
        for index, key in enumerate(sorted(response.data['data'].keys())):
            if key in ['Age', 'DOB', 'HospNo', 'Status']:
                continue
            if not response.data['data'][key]:
                family_member_info[key] = None

            family_member_info[sorted_keys[index]] = response.data['data'][key]
        family_member_info['uhid_number'] = uhid_number
        family_member_info['patient_info'] = patient_info
        family_member_info['raw_info_from_manipal_API'] = response.data['data']
        family_member_obj = self.model.objects.create(**family_member_info)
        serializer = self.get_serializer(family_member_obj)
        data = {
            "data": serializer.data,
            "message": "Your family member is added successfully!"
        }
        return Response(data, status=status.HTTP_201_CREATED)


