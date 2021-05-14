import logging
import base64
import hashlib
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.contrib.gis.geos import Point
from django.utils.crypto import get_random_string
from django.utils.decorators import method_decorator
from apps.master_data.models import Company
from apps.master_data.views import ValidateMobileView, ValidateUHIDView
from apps.dashboard.utils import DashboardUtils
from apps.patient_registration.models import Relation
from axes.models import AccessAttempt
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView
from rest_framework_jwt.utils import jwt_encode_handler, jwt_payload_handler
from ratelimit.decorators import ratelimit
from utils import custom_viewsets
from utils.custom_sms import send_sms
from utils.custom_permissions import (
                                BlacklistDestroyMethodPermission,
                                BlacklistUpdateMethodPermission,
                                IsManipalAdminUser, IsPatientUser,
                                IsSelfAddress, IsSelfFamilyMember,
                                SelfUserAccess
                            )
from utils.custom_jwt_whitelisted_tokens import WhiteListedJWTTokenUtil
from utils.utils import manipal_admin_object, patient_user_object, assign_users
from .emails import (
                send_corporate_email_activation_otp,
                send_email_activation_otp,
                send_family_member_email_activation_otp
            )
from .exceptions import (
                    InvalidCredentialsException, 
                    InvalidEmailOTPException,
                    OTPExpiredException,
                    PatientDoesNotExistsValidationException,
                    PatientMobileDoesNotExistsValidationException,
                    PatientMobileExistsValidationException,
                    MobileAppVersionValidationException
                )
from .serializers import (  
                    CovidVaccinationRegistrationSerializer, FamilyMemberSerializer, 
                    PatientAddressSerializer,
                    PatientSerializer, FamilyMemberCorporateHistorySerializer
                )
from .utils import covid_registration_mandatory_check, fetch_uhid_user_details, link_uhid
from .models import CovidVaccinationRegistration, FamilyMember, OtpGenerationCount, Patient, PatientAddress, FamilyMemberCorporateHistory
from .constants import PatientsConstants
from utils.custom_validation import ValidationUtil
logger = logging.getLogger('django')
OTP_LENGTH = settings.OTP_LENGTH

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
    search_fields = ['first_name','last_name','mobile', 'email','uhid_number']
    ordering_fields = ('-created_at',)

    def get_queryset(self):
        admin_object = manipal_admin_object(self.request)
        if admin_object and admin_object.hospital:
            location_id = admin_object.hospital.id
            return Patient.objects.filter(favorite_hospital__id=location_id)
        return super().get_queryset().distinct()

    def get_permissions(self):

        if self.action in ['create', 'verify_login_otp', 'generate_login_otp', ]:
            permission_classes = [AllowAny]
            return [permission() for permission in permission_classes]

        if self.action in ['generate_uhid_otp', 'validate_uhid_otp',
                           'generate_email_verification_otp', 'verify_email_otp',
                           'generate_new_mobile_verification_otp', 'verify_new_mobile_otp', 'switch_view',
                           'verify_corporate_email_otp', 'generate_corporate_email_verification_otp']:
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

        app_version = self.request.query_params.get("version", None)
        if  app_version and \
            DashboardUtils.check_if_version_update_enabled() and \
            DashboardUtils.check_if_version_update_required(app_version):
            raise MobileAppVersionValidationException

        facebook_id = self.request.data.get('facebook_id')
        google_id = self.request.data.get('google_id')
        apple_id = self.request.data.get("apple_id")

        patient_obj = self.get_queryset().filter(
            mobile=self.request.data.get('mobile')).first()

        if patient_obj:

            if not (facebook_id or google_id or apple_id) and patient_obj.mobile_verified == True:
                raise PatientMobileExistsValidationException

            if patient_obj.mobile_verified == False:
                patient_obj.delete()
                patient_obj = None

        random_password = get_random_string(length=OTP_LENGTH, allowed_chars='0123456789')
        otp_expiration_time = datetime.now() + timedelta(seconds=int(settings.OTP_EXPIRATION_TIME))

        if patient_obj:
            patient_obj.set_password(random_password)
            patient_obj.otp_expiration_time = otp_expiration_time
            patient_obj.save()
            self.serializer = self.get_serializer(patient_obj)
            user_obj = patient_obj

        else:
            user_obj = serializer.save(
                otp_expiration_time=otp_expiration_time,
                is_active=True)

            user_obj.set_password(random_password)
            user_obj.save()

        
        otp_instance = OtpGenerationCount.objects.filter(mobile=user_obj.mobile).first()
        if not otp_instance:
            otp_instance = OtpGenerationCount.objects.create(mobile=user_obj.mobile, otp_generation_count=1)

        current_time = datetime.today()
        delta = current_time - otp_instance.updated_at
        if delta.seconds <= 600 and otp_instance.otp_generation_count >= 3:
            raise ValidationError(
                "You have reached Maximum Otp generation Limit. Please try after 10 minutes")

        if delta.seconds > 600:
            otp_instance.otp_generation_count = 1
            otp_instance.save()

        if delta.seconds <= 600:
            otp_instance.otp_generation_count += 1
            otp_instance.save()


        message = "OTP to activate your account is {}, this OTP will expire in {} seconds.".format(
            random_password, settings.OTP_EXPIRATION_TIME)
        if self.request.query_params.get('is_android', True):
            message = '<#> ' + message + ' ' + settings.ANDROID_SMS_RETRIEVER_API_KEY
        is_message_sent = send_sms(mobile_number=str(
            user_obj.mobile.raw_input), message=message)
        if is_message_sent:
            self.create_success_message = 'Your registration is completed successfully. Activate your account by entering the OTP which we have sent to your mobile number.'
        else:
            self.create_success_message = 'Your registration completed successfully, we are unable to send OTP to your number. Please try after sometime.'
    
    def perform_update(self, serializer):
        patient_object = self.get_object()

        if 'new_mobile' in serializer.validated_data and\
                not patient_object.mobile == serializer.validated_data['new_mobile']:

            if Patient.objects.filter(mobile=serializer.validated_data['new_mobile']).exists():
                raise ValidationError(
                    "This mobile number is already registered with us, please try with another number!")

            otp_instance = OtpGenerationCount.objects.filter(mobile=serializer.validated_data['new_mobile']).first()
            if not otp_instance:
                otp_instance = OtpGenerationCount.objects.create(mobile=serializer.validated_data['new_mobile'], otp_generation_count=1)

            current_time = datetime.today()
            delta = current_time - otp_instance.updated_at
            if delta.seconds <= 600 and otp_instance.otp_generation_count >= 3:
                raise ValidationError(
                    "You have reached Maximum Otp generation Limit. Please try after 10 minutes")

            if delta.seconds > 600:
                otp_instance.otp_generation_count = 1
                otp_instance.save()

            if delta.seconds <= 600:
                otp_instance.otp_generation_count += 1
                otp_instance.save()


            random_mobile_change_password = get_random_string(length=OTP_LENGTH, allowed_chars='0123456789')
            otp_expiration_time = datetime.now() + timedelta(seconds=int(settings.OTP_EXPIRATION_TIME))

            patient_object = serializer.save()
            patient_object.new_mobile_verification_otp = random_mobile_change_password
            patient_object.new_mobile_otp_expiration_time = otp_expiration_time
            patient_object.save()

            message = "OTP to activate your new mobile number is {}, this OTP will expire in {} seconds.".format(
                random_mobile_change_password, settings.OTP_EXPIRATION_TIME)

            if self.request.query_params.get('is_android', True):
                message = '<#> ' + message + ' ' + settings.ANDROID_SMS_RETRIEVER_API_KEY
            is_message_sent = send_sms(mobile_number=str(
                patient_object.new_mobile.raw_input), message=message)
            if is_message_sent:
                self.update_success_message = 'Enter the OTP which we have sent to your new mobile number to activate.'
            else:
                self.update_success_message = 'We are unable to send OTP to your new mobile number. Please try after sometime.'

            return

        if 'email' in serializer.validated_data and \
                not patient_object.email == serializer.validated_data['email']:
            patient_object = serializer.save(
                email_verified=False)

            random_email_otp = get_random_string(
                length=OTP_LENGTH, allowed_chars='0123456789')
            otp_expiration_time = datetime.now(
            ) + timedelta(seconds=int(settings.OTP_EXPIRATION_TIME))

            # send_email_activation_otp(str(patient_object.id), random_email_otp)

            patient_object.email_otp = random_email_otp
            patient_object.email_otp_expiration_time = otp_expiration_time
            patient_object.save()
            self.update_success_message = "Your email is changed, please enter the OTP to verify."
        else:
            serializer.save()

    @method_decorator(ratelimit(key=settings.RATELIMIT_KEY_IP, rate=settings.RATELIMIT_OTP_GENERATION, block=True, method=ratelimit.ALL))
    @action(detail=False, methods=['POST'])
    def verify_login_otp(self, request):
        username = request.data.get('mobile')
        password = request.data.get('password') or request.data.get('otp')
        facebook_id = self.request.data.get('facebook_id')
        google_id = self.request.data.get('google_id')
        apple_id = self.request.data.get("apple_id")
        apple_email = self.request.data.get("apple_email")
        email = self.request.data.get("email")

        if not (username and password):
            raise InvalidCredentialsException

        authenticated_patient = authenticate(request=request, username=username,
                                             password=password)

        access_log = AccessAttempt.objects.filter(username=username).first()
        if not authenticated_patient:
            if access_log:
                attempt = access_log.failures_since_start
                if attempt < 3:
                    message = settings.WRONG_OTP_ATTEMPT_ERROR.format(attempt)
                    raise ValidationError(message)
                if attempt >= 3:
                    message = settings.MAX_WRONG_OTP_ATTEMPT_ERROR
                    raise ValidationError(message)
            raise InvalidCredentialsException

        if access_log:
            access_log.delete()

        if datetime.now().timestamp() > authenticated_patient.otp_expiration_time.timestamp():
            raise OTPExpiredException
        message = "Login successful!"

        if authenticated_patient.mobile_verified:
            if email:
                authenticated_patient.email = email
            if facebook_id:
                authenticated_patient.facebook_id = facebook_id
            if google_id:
                authenticated_patient.google_id = google_id
            if apple_id:
                authenticated_patient.apple_id = apple_id
                authenticated_patient.apple_email = apple_email
            authenticated_patient.save()

        update_last_login(None, authenticated_patient)
        if not authenticated_patient.mobile_verified:
            authenticated_patient.mobile_verified = True
            message = "Your account is activated successfully!"
        random_password = get_random_string(
            length=OTP_LENGTH, allowed_chars='0123456789')
        authenticated_patient.set_password(random_password)
        authenticated_patient.save()
        
        serializer = self.get_serializer(authenticated_patient)
        payload = jwt_payload_handler(authenticated_patient)
        payload['username'] = payload['username'].raw_input
        payload['mobile'] = payload['mobile'].raw_input
        token = jwt_encode_handler(payload)
        expiration = datetime.utcnow() + settings.JWT_AUTH['JWT_EXPIRATION_DELTA']
        expiration_epoch = expiration.timestamp()

        otp_instance = OtpGenerationCount.objects.filter(mobile=authenticated_patient.mobile).first()
        if otp_instance:
            otp_instance.otp_generation_count = 0
            otp_instance.save()

        WhiteListedJWTTokenUtil.create_token(authenticated_patient,token)

        data = {
            "data": serializer.data,
            "message": message,
            "token": token,
            "token_expiration": expiration_epoch
        }
        return Response(data, status=status.HTTP_200_OK)

    @method_decorator(ratelimit(key=settings.RATELIMIT_KEY_USER_OR_IP, rate=settings.RATELIMIT_OTP_GENERATION, block=True, method=ratelimit.ALL))
    @action(detail=False, methods=['PATCH'])
    def verify_new_mobile_otp(self, request):
        new_mobile_otp = request.data.get('new_mobile_otp')
        if not new_mobile_otp:
            raise ValidationError("Enter OTP to verify new mobile number!")
        patient_obj = patient_user_object(request)

        if not patient_obj.new_mobile_verification_otp == new_mobile_otp:
            raise ValidationError(PatientsConstants.INVALID_OTP)

        if datetime.now().timestamp() > \
                patient_obj.new_mobile_otp_expiration_time.timestamp():
            raise OTPExpiredException

        if Patient.objects.filter(mobile=patient_obj.new_mobile).exists():
            raise ValidationError(
                "This mobile number is registered with us recently, please try with another number!")

        message = "Successfully changed your mobile number, please login again!"

        random_password = get_random_string(
            length=OTP_LENGTH, allowed_chars='0123456789')

        patient_obj.new_mobile_verification_otp = random_password
        patient_obj.mobile = patient_obj.new_mobile
        patient_obj.save()

        serializer = self.get_serializer(patient_obj)

        data = {
            "data": serializer.data,
            "message": message,
        }
        return Response(data, status=status.HTTP_200_OK)

    @method_decorator(ratelimit(key=settings.RATELIMIT_KEY_USER_OR_IP, rate=settings.RATELIMIT_OTP_GENERATION, block=True, method=ratelimit.ALL))
    @action(detail=False, methods=['GET'])
    def generate_new_mobile_verification_otp(self, request):
        patient_obj = patient_user_object(request)

        if not patient_obj.new_mobile or patient_obj.mobile == patient_obj.new_mobile:
            raise ValidationError(PatientsConstants.INVALID_REQUEST)

        random_mobile_change_password = get_random_string(
            length=OTP_LENGTH, allowed_chars='0123456789')

        otp_expiration_time = datetime.now(
        ) + timedelta(seconds=int(settings.OTP_EXPIRATION_TIME))

        patient_obj.new_mobile_verification_otp = random_mobile_change_password
        patient_obj.new_mobile_otp_expiration_time = otp_expiration_time
        patient_obj.save()

        mobile_number = str(patient_obj.new_mobile.raw_input)
        message = "OTP to activate your new mobile number is {}, this OTP will expire in {} seconds.".format(
            random_mobile_change_password, settings.OTP_EXPIRATION_TIME)

        if self.request.query_params.get('is_android', True):
            message = '<#> ' + message + ' ' + settings.ANDROID_SMS_RETRIEVER_API_KEY
        is_message_sent = send_sms(mobile_number=mobile_number, message=message)
        if is_message_sent:
            response_message = 'Enter the OTP which we have sent to your new mobile number to activate.'
        else:
            response_message = 'We are unable to send OTP to your new mobile number. Please try after sometime.'

        data = {
            "data": {"mobile": mobile_number},
            "message": response_message,
        }
        return Response(data, status=status.HTTP_200_OK)

    @method_decorator(ratelimit(key=settings.RATELIMIT_KEY_USER_OR_IP, rate=settings.RATELIMIT_OTP_GENERATION, block=True, method=ratelimit.ALL))
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
            length=OTP_LENGTH, allowed_chars='0123456789')

        authenticated_patient.email_otp = random_email_otp
        authenticated_patient.email_verified = True
        authenticated_patient.save()

        authenticated_patient.patient_family_member_info.filter(is_visible=True,
                                                                email=authenticated_patient.email).update(email_verified=True)

        data = {
            "data": self.get_serializer(authenticated_patient).data,
            "message": "Your email is verified successfully!"
        }
        return Response(data, status=status.HTTP_200_OK)

    @method_decorator(ratelimit(key=settings.RATELIMIT_KEY_USER_OR_IP, rate=settings.RATELIMIT_OTP_GENERATION, block=True, method=ratelimit.ALL))
    @action(detail=False, methods=['GET'])
    def generate_email_verification_otp(self, request):
        authenticated_patient = patient_user_object(request)

        if authenticated_patient.email_verified:
            raise ValidationError(PatientsConstants.INVALID_REQUEST)

        random_email_otp = get_random_string(
            length=OTP_LENGTH, allowed_chars='0123456789')
        otp_expiration_time = datetime.now(
        ) + timedelta(seconds=int(settings.OTP_EXPIRATION_TIME))

        send_email_activation_otp(
            str(authenticated_patient.id), random_email_otp)

        authenticated_patient.email_otp = random_email_otp
        authenticated_patient.email_otp_expiration_time = otp_expiration_time
        authenticated_patient.save()

        data = {
            "data": {"email": str(authenticated_patient.email), },
            "message": PatientsConstants.OTP_EMAIL_SENT,
        }
        return Response(data, status=status.HTTP_200_OK)

    @method_decorator(ratelimit(key=settings.RATELIMIT_KEY_IP, rate=settings.RATELIMIT_OTP_GENERATION, block=True, method=ratelimit.ALL))
    @action(detail=False, methods=['POST'])
    def generate_login_otp(self, request):

        app_version = self.request.query_params.get("version", None)
        data = {}
        if  app_version and \
            DashboardUtils.check_if_version_update_enabled() and \
            DashboardUtils.check_if_version_update_required(app_version):
            
            data["force_update_enable"] = settings.FORCE_UPDATE_ENABLE
            data["force_update_required"] = DashboardUtils.check_if_version_update_required(app_version)
            return Response(data, status=status.HTTP_200_OK)

        mobile = request.data.get('mobile')
        facebook_id = request.data.get('facebook_id')
        google_id = request.data.get('google_id')
        apple_id = request.data.get("apple_id")
        apple_email = request.data.get("apple_email")
        sign_up = request.data.get("sign_up")

        if not (mobile or facebook_id or google_id or apple_id):
            raise PatientDoesNotExistsValidationException

        if mobile:
            request_patient = self.get_queryset().filter(
                mobile=mobile).first()
            if not request_patient:
                raise PatientMobileDoesNotExistsValidationException

            otp_instance = OtpGenerationCount.objects.filter(
                mobile=mobile).first()
            if not otp_instance:
                otp_instance = OtpGenerationCount.objects.create(
                    mobile=mobile, otp_generation_count=1)

            current_time = datetime.today()
            delta = current_time - otp_instance.updated_at
            if delta.seconds <= 600 and otp_instance.otp_generation_count >= 3:
                raise ValidationError(
                    "You have reached Maximum Otp generation Limit. Please try after 10 minutes")

            if delta.seconds > 600:
                otp_instance.otp_generation_count = 1
                otp_instance.save()

            if delta.seconds <= 600:
                otp_instance.otp_generation_count += 1
                otp_instance.save()

        if facebook_id:
            request_patient = self.get_queryset().filter(
                facebook_id=facebook_id).first()
        if google_id:
            request_patient = self.get_queryset().filter(
                google_id=google_id).first()
        if apple_id:
            request_patient = self.get_queryset().filter(
                apple_id=apple_id).first()

        if not request_patient:
            raise PatientDoesNotExistsValidationException

        if request_patient.mobile_verified == False and not sign_up:
            raise PatientMobileDoesNotExistsValidationException

        if (facebook_id or google_id or apple_id):

            serializer = self.get_serializer(request_patient)
            if apple_email:
                request_patient.apple_email = apple_email
                request_patient.save()

            payload = jwt_payload_handler(request_patient)
            payload['username'] = payload['username'].raw_input
            payload['mobile'] = payload['mobile'].raw_input
            token = jwt_encode_handler(payload)
            expiration = datetime.utcnow() + settings.JWT_AUTH['JWT_EXPIRATION_DELTA']
            expiration_epoch = expiration.timestamp()

            WhiteListedJWTTokenUtil.create_token(request_patient,token)

            message = "Login successful!"
            data = {
                "data": serializer.data,
                "message": message,
                "token": token,
                "token_expiration": expiration_epoch
            }
            return Response(data, status=status.HTTP_200_OK)

        random_password = get_random_string(
            length=OTP_LENGTH, allowed_chars='0123456789')

        if str(request_patient.mobile) == settings.HARDCODED_MOBILE_NO:
            random_password = settings.HARDCODED_MOBILE_OTP

        otp_expiration_time = datetime.now(
        ) + timedelta(seconds=int(settings.OTP_EXPIRATION_TIME))

        request_patient.otp_expiration_time = otp_expiration_time
        request_patient.set_password(random_password)
        request_patient.save()

        message = "OTP to login into your account is {}, this OTP will expire in {} seconds".format(
            random_password, settings.OTP_EXPIRATION_TIME)
        if not request_patient.is_active:
            message = "OTP to activate your account is {}, this OTP will expire in {} seconds".format(
                random_password, settings.OTP_EXPIRATION_TIME)

        if self.request.query_params.get('is_android', True):
            message = '<#> ' + message + ' ' + settings.ANDROID_SMS_RETRIEVER_API_KEY
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
        
        if not uhid_number:
            raise ValidationError(PatientsConstants.ENTER_VALID_UHID)

        patient_info = patient_user_object(request)
        if patient_info.uhid_number == uhid_number:
            raise ValidationError(
                "This UHID is already linked to your account!")

        if self.model.objects.filter(uhid_number=uhid_number).exists():
            raise ValidationError(
                "There is an exisiting user  on our platform with this UHID.")

        if FamilyMember.objects.filter(patient_info=patient_info,
                                       uhid_number=uhid_number,
                                       is_visible=True).exists():
            raise ValidationError(PatientsConstants.UHID_LINKED_TO_FAMILY_MEMBER)
        uhid_user_info = fetch_uhid_user_details(request)

        patient_user_obj = self.get_object()

        patient_user_obj.first_name = uhid_user_info['first_name']
        patient_user_obj.last_name = None
        patient_user_obj.middle_name = None
        if uhid_user_info['email']:
            patient_user_obj.email = uhid_user_info['email']
            patient_user_obj.email_verified = True
        patient_user_obj.gender = uhid_user_info['gender']

        patient_user_obj.uhid_number = uhid_number
        patient_user_obj.save()
        data = {
            "data": self.get_serializer(self.get_object()).data,
            "message": "Your UHID is updated successfully!"
        }
        link_uhid(request)
        return Response(data, status=status.HTTP_201_CREATED)

    @method_decorator(ratelimit(key=settings.RATELIMIT_KEY_USER_OR_IP, rate=settings.RATELIMIT_OTP_GENERATION, block=True, method=ratelimit.ALL))
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

    @method_decorator(ratelimit(key=settings.RATELIMIT_KEY_USER_OR_IP, rate=settings.RATELIMIT_OTP_GENERATION, block=True, method=ratelimit.ALL))
    @action(detail=False, methods=['POST'])
    def validate_uhid_otp(self, request):
        uhid_user_info = fetch_uhid_user_details(request)
        data = {
            "data": uhid_user_info,
            "message": "Fetched user details!"
        }
        link_uhid(request)
        return Response(data, status=status.HTTP_200_OK)

    @method_decorator(ratelimit(key=settings.RATELIMIT_KEY_USER_OR_IP, rate=settings.RATELIMIT_OTP_GENERATION, block=True, method=ratelimit.ALL))
    @action(detail=False, methods=['POST'])
    def generate_corporate_email_verification_otp(self, request):
        authenticated_patient = patient_user_object(request)
        company_name = self.request.data.get("company_name")
        corporate_email = self.request.data.get("corporate_email")

        if company_name:
            company_instance = Company.objects.filter(
                name=company_name).first()

        random_email_otp = get_random_string(length=OTP_LENGTH, allowed_chars='0123456789')
        otp_expiration_time = datetime.now(
        ) + timedelta(seconds=int(settings.OTP_EXPIRATION_TIME))

        send_corporate_email_activation_otp(str(authenticated_patient.id), corporate_email, random_email_otp)

        if company_instance:
            authenticated_patient.company_info = company_instance
            authenticated_patient.corporate_email = corporate_email

        authenticated_patient.corporate_email_otp = random_email_otp
        authenticated_patient.corporate_email_otp_expiration_time = otp_expiration_time
        authenticated_patient.save()

        data = {
            "data": {"email": str(authenticated_patient.corporate_email), },
            "message": PatientsConstants.OTP_EMAIL_SENT,
        }
        return Response(data, status=status.HTTP_200_OK)

    @method_decorator(ratelimit(key=settings.RATELIMIT_KEY_USER_OR_IP, rate=settings.RATELIMIT_OTP_GENERATION, block=True, method=ratelimit.ALL))
    @action(detail=False, methods=['POST'])
    def verify_corporate_email_otp(self, request):
        email_otp = request.data.get('email_otp')
        authenticated_patient = patient_user_object(request)

        if not authenticated_patient.corporate_email_otp == email_otp:
            raise InvalidEmailOTPException

        if datetime.now().timestamp() > \
                authenticated_patient.corporate_email_otp_expiration_time.timestamp():
            raise OTPExpiredException

        random_email_otp = get_random_string(
            length=OTP_LENGTH, allowed_chars='0123456789')

        authenticated_patient.corporate_email_otp = random_email_otp
        authenticated_patient.active_view = "Corporate"
        authenticated_patient.is_corporate = True
        family_members_ids = FamilyMember.objects.filter(patient_info = authenticated_patient.id)
        if family_members_ids and authenticated_patient.company_info:
            for family_member in family_members_ids:
                family_members_history = FamilyMemberCorporateHistory.objects.filter(
                                                                family_member = family_member.id, 
                                                                company_info = authenticated_patient.company_info.id
                                                            ).first()
                if family_members_history:
                    family_member.is_corporate = True
                    family_member.save()
        authenticated_patient.save()

        data = {
            "data": self.get_serializer(authenticated_patient).data,
            "message": "Your email is verified successfully!"
        }
        return Response(data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['POST'])
    def unlink_corporate_email(self,request):
        authenticated_patient = patient_user_object(request)
        authenticated_patient.company_info = None
        authenticated_patient.corporate_email = None
        authenticated_patient.active_view = "Normal"
        authenticated_patient.is_corporate = False
        family_members_ids = FamilyMember.objects.filter(patient_info=authenticated_patient.id)
        if family_members_ids:
             family_members_ids.update(is_corporate=False)
        authenticated_patient.save()
        data = {
            "data": self.get_serializer(authenticated_patient).data,
            "message": "Your corporate email is unlinked successfully!"
        }
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'])
    def switch_view(self, request):
        patient = Patient.objects.filter(id=request.user.id).first()
        view = request.data.get("view", None)
        if view not in ["Normal", "Corporate"] or not patient.is_corporate:
            raise ValidationError("View Not Acceptable")

        if not patient:
            raise ValidationError("You are not a User")
        patient.active_view = view
        patient.save()
        serialize_data = PatientSerializer(patient)

        data = {
            "data": serialize_data.data,
            "message": PatientsConstants.OTP_EMAIL_SENT,
        }
        return Response(data, status=status.HTTP_200_OK)

    @method_decorator(ratelimit(key=settings.RATELIMIT_KEY_USER_OR_IP, rate=settings.RATELIMIT_OTP_GENERATION, block=True, method=ratelimit.ALL))
    @action(detail=False, methods=['POST'])
    def generate_mobile_uhid_otp(self, request):
        mobile = request.data.get('mobile')
        if not mobile:
            raise ValidationError('Mobile number is missing')

        factory = APIRequestFactory()
        proxy_request = factory.post('', {"mobile_no": mobile}, format='json')
        response = ValidateMobileView.as_view()(proxy_request)

        if not (response.status_code == 200 and response.data['success']):
            raise ValidationError(response.data['message'])

        data = {
            "data": None,
            "message": response.data['message'],
        }
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'])
    def mobile_uhid_link(self, request):
        patient = Patient.objects.filter(id=request.user.id).first()
        if not patient:
            raise ValidationError("You are not a User")
        
        uhid_number=request.data.get("uhid_number")
        if not uhid_number:
            raise ValidationError('UHID is missing!')

        user_id=request.data.get("user_id")
        family_member=FamilyMember.objects.filter(
            patient_info=patient, is_visible=True)

        if user_id:
            member=family_member.filter(id=user_id).first()
            if not member:
                raise ValidationError("Family Member not Available")

            if patient.uhid_number == uhid_number:
                raise ValidationError(PatientsConstants.CANT_ASSOCIATE_UHID_TO_FAMILY_MEMBER)

            if family_member.filter(uhid_number=uhid_number).exists():
                raise ValidationError(PatientsConstants.UHID_LINKED_TO_FAMILY_MEMBER)

            member.uhid_number = uhid_number
            member.first_name = request.data.get("first_name", None)
            member.last_name = None
            member.middle_name = None
            member.mobile = request.data.get("mobile", None)
            member.age = request.data.get("age", None)
            member.gender = request.data.get("gender", None)
            if request.data.get("email", None):
                member.email = request.data.get("email", None)
                member.email_verified = True
            member.save()

            serialize_data = FamilyMemberSerializer(family_member, many=True)

        else:
            if patient.uhid_number == uhid_number:
                raise ValidationError("This UHID is already linked to your account!")
                
            if self.model.objects.filter(uhid_number=uhid_number).exists():
                raise ValidationError("There is an exisiting user  on our platform with this UHID.")
            
            if FamilyMember.objects.filter(patient_info=patient,uhid_number=uhid_number,is_visible=True).exists():
                raise ValidationError(PatientsConstants.UHID_LINKED_TO_FAMILY_MEMBER)

            patient.uhid_number = uhid_number
            patient.first_name = request.data.get("first_name", None)
            patient.age = request.data.get("age", None)
            patient.gender = request.data.get("gender", None)
            patient.last_name = None
            patient.middle_name = None
            if request.data.get("email", None):
                patient.email = request.data.get("email", None)
                patient.email_verified = True
            patient.save()

            serialize_data = PatientSerializer(patient)

        data={
            "data": serialize_data.data,
            "message": "fetched user details",
        }
        link_uhid(request)
        return Response(data, status=status.HTTP_200_OK)


class FamilyMemberViewSet(custom_viewsets.ModelViewSet):
    permission_classes=[IsAuthenticated]
    model=FamilyMember
    queryset=FamilyMember.objects.all().order_by('created_at')
    serializer_class=FamilyMemberSerializer
    create_success_message='Your family member has been added successfully!'
    list_success_message='Family members list returned successfully!'
    retrieve_success_message='Information returned successfully!'
    update_success_message='Information updated successfully!'
    delete_success_message='Your family member account is deleted successfully!'

    filter_backends=(DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    filter_fields=['is_corporate']
    search_fields=['first_name','uhid_number' ]
    ordering_fields=('-created_at',)

    def get_permissions(self):
        if self.action in ['create', ]:
            permission_classes=[IsPatientUser]
            return [permission() for permission in permission_classes]

        if self.action in ['partial_update', 'retrieve',
                           'verify_family_member_email_otp',
                           'verify_family_member_otp',
                           'generate_family_member_mobile_verification_otp',
                           'generate_family_member_email_verification_otp']:
            permission_classes=[IsPatientUser & IsSelfFamilyMember]
            return [permission() for permission in permission_classes]

        if self.action == 'list':
            permission_classes=[IsManipalAdminUser | IsPatientUser]
            return [permission() for permission in permission_classes]

        if self.action == 'update':
            permission_classes=[BlacklistUpdateMethodPermission]
            return [permission() for permission in permission_classes]

        return super().get_permissions()
    
    def get_patient_info_object(self):
        request_patient_info = None
        try:
            if self.request.query_params.get('patient_id'):
                request_patient_info = Patient.objects.get(id=self.request.query_params.get('patient_id'))
        except Exception as error:
            logger.error("Exception in FamilyMemberViewSet %s"%(str(error)))
        if not request_patient_info:
            raise ValidationError("Invalid patient information.")
        return request_patient_info
    
    def get_queryset(self):
        qs=super().get_queryset().filter(patient_info__id=self.request.user.id,is_visible=True)
        admin_object = manipal_admin_object(self.request)
        if admin_object:
            request_patient_info = self.get_patient_info_object()
            if admin_object.hospital:
                location_id = admin_object.hospital.id
                return FamilyMember.objects.filter(
                        patient_info__id=request_patient_info.id,
                        is_visible=True,
                        patient_info__favorite_hospital__id=location_id
                    )
            qs=FamilyMember.objects.filter(
                        patient_info__id=request_patient_info.id,
                        is_visible=True
                    )
        return qs

    def perform_create(self, serializer):
        if self.get_queryset().count() >= int(settings.MAX_FAMILY_MEMBER_COUNT):
            raise ValidationError(PatientsConstants.REACHED_LIMIT_FAMILY_MEMBER)

        if not 'email' in serializer.validated_data or not serializer.validated_data['email']:
            raise ValidationError("Email is not mentioned!")

        random_mobile_password=get_random_string(
            length=OTP_LENGTH, allowed_chars='0123456789')
        otp_expiration_time=datetime.now(
        ) + timedelta(seconds=int(settings.OTP_EXPIRATION_TIME))

        is_mobile_to_be_verified=True
        is_email_to_be_verified=True
        is_visible=False

        request_patient=patient_user_object(self.request)

        if serializer.validated_data['mobile'] == request_patient.mobile:
            is_mobile_to_be_verified=False
            is_visible=True

        if serializer.validated_data['email'] == request_patient.email and request_patient.email_verified:
            is_email_to_be_verified=False

        user_obj=serializer.save(
            mobile_otp_expiration_time=otp_expiration_time,
            mobile_verification_otp=random_mobile_password,
            mobile_verified=not is_mobile_to_be_verified,
            email_verified=not is_email_to_be_verified,
            is_visible=is_visible
        )

        self.create_success_message="Family member is added successfully!"

        if is_mobile_to_be_verified:

            otp_instance = OtpGenerationCount.objects.filter(mobile=user_obj.mobile).first()
            if not otp_instance:
                otp_instance = OtpGenerationCount.objects.create(mobile=user_obj.mobile, otp_generation_count=1)

            current_time = datetime.today()
            delta = current_time - otp_instance.updated_at
            if delta.seconds <= 600 and otp_instance.otp_generation_count >= 5:
                raise ValidationError(
                    "You have reached Maximum Otp generation Limit. Please try after 10 minutes")

            if delta.seconds > 600:
                otp_instance.otp_generation_count = 1
                otp_instance.save()

            if delta.seconds <= 600:
                otp_instance.otp_generation_count += 1
                otp_instance.save()

            message="You have been added as a family member on Manipal Hospital application by\
            {}, OTP to activate your account is {}, this OTP will expire in {} seconds".format(
                ValidationUtil.refine_text_only(request_patient.first_name),
                random_mobile_password, settings.OTP_EXPIRATION_TIME)

            if self.request.query_params.get('is_android', True):
                message='<#> ' + message + ' ' + settings.ANDROID_SMS_RETRIEVER_API_KEY
            is_message_sent=send_sms(mobile_number=str(
                user_obj.mobile.raw_input), message=message)
            if is_message_sent:
                self.create_success_message='Please enter OTP which we have sent to your family member.'
            else:
                self.create_success_message='We are unable to send OTP to your family member. Please try after sometime.'

    def perform_update(self, serializer):
        request_patient=patient_user_object(self.request)
        family_member_object=self.get_object()
        is_email_to_be_verified=False
        is_mobile_to_be_verified=False

        if 'is_corporate' in serializer.validated_data and \
            serializer.validated_data['is_corporate'] and \
            family_member_object.patient_info and \
            family_member_object.patient_info.company_info:

            mapping_id = FamilyMemberCorporateHistory.objects.filter(family_member = family_member_object.id, company_info = family_member_object.patient_info.company_info.id)

            if not mapping_id:
                data = {
                    "family_member" : family_member_object.id,
                    "company_info"  : family_member_object.patient_info.company_info.id
                }
                FamilyMemberCorporateHistorySerializer(data=data)
                FamilyMemberCorporateHistorySerializer.save()

        if 'new_mobile' in serializer.validated_data and not family_member_object.mobile == serializer.validated_data['new_mobile']:
            if not serializer.validated_data['new_mobile'] == str(request_patient.mobile.raw_input):
                is_mobile_to_be_verified=True
            else:
                serializer.validated_data['mobile']=serializer.validated_data['new_mobile']

        if 'email' in serializer.validated_data and not family_member_object.email == serializer.validated_data['email']:

            is_email_to_be_verified=True

            if serializer.validated_data['email'] == request_patient.email and request_patient.email_verified:
                is_email_to_be_verified=False

            family_member_object=serializer.save(
                email_verified=not is_email_to_be_verified)
        else:
            family_member_object=serializer.save()

        if is_email_to_be_verified:
            random_email_otp=get_random_string(
                length=OTP_LENGTH, allowed_chars='0123456789')
            otp_expiration_time=datetime.now(
            ) + timedelta(seconds=int(settings.OTP_EXPIRATION_TIME))

            family_member_object.email_verified=False
            family_member_object.email_verification_otp=random_email_otp
            family_member_object.email_otp_expiration_time=otp_expiration_time
            family_member_object.save()

            # send_family_member_email_activation_otp(
            #     str(family_member_object.id), random_email_otp)

        if is_mobile_to_be_verified:

            otp_instance = OtpGenerationCount.objects.filter(mobile=family_member_object.new_mobile).first()
            if not otp_instance:
                otp_instance = OtpGenerationCount.objects.create(mobile=family_member_object.new_mobile, otp_generation_count=1)

            current_time = datetime.today()
            delta = current_time - otp_instance.updated_at
            if delta.seconds <= 600 and otp_instance.otp_generation_count >= 3:
                raise ValidationError(
                    "You have reached Maximum Otp generation Limit. Please try after 10 minutes")

            if delta.seconds > 600:
                otp_instance.otp_generation_count = 1
                otp_instance.save()

            if delta.seconds <= 600:
                otp_instance.otp_generation_count += 1
                otp_instance.save()

            random_mobile_password=get_random_string(
                length=OTP_LENGTH, allowed_chars='0123456789')
            otp_expiration_time=datetime.now(
            ) + timedelta(seconds=int(settings.OTP_EXPIRATION_TIME))

            family_member_object.mobile_verification_otp=random_mobile_password
            family_member_object.mobile_otp_expiration_time=otp_expiration_time
            family_member_object.save()

            message="Your mobile number has been added on Manipal Hospital application by\
            {}, OTP to activate your account is {}, this OTP will expire in {} seconds".format(
                ValidationUtil.refine_text_only(request_patient.first_name),
                random_mobile_password, settings.OTP_EXPIRATION_TIME)

            if self.request.query_params.get('is_android', True):
                message='<#> ' + message + ' ' + settings.ANDROID_SMS_RETRIEVER_API_KEY
            is_message_sent=send_sms(mobile_number=str(
                family_member_object.new_mobile.raw_input), message=message)
            if is_message_sent:
                self.update_success_message='Family member details updated successfully, please enter OTP which we have sent to your family member.'
            else:
                self.update_success_message='Family member detials updated successfully, we are unable to send OTP to your family member. Please try after sometime.'

    def perform_destroy(self, instance):
        instance.is_visible=False
        instance.save()

    @action(detail=False, methods=['POST'])
    def validate_new_family_member_uhid_otp(self, request):
        if self.get_queryset().count() >= int(settings.MAX_FAMILY_MEMBER_COUNT):
            raise ValidationError(PatientsConstants.REACHED_LIMIT_FAMILY_MEMBER)

        uhid_number=request.data.get('uhid_number')
        if not uhid_number:
            raise ValidationError(PatientsConstants.ENTER_VALID_UHID)

        patient_info=patient_user_object(request)
        if patient_info.uhid_number == uhid_number:
            raise ValidationError(PatientsConstants.CANT_ASSOCIATE_UHID_TO_FAMILY_MEMBER)

        if self.model.objects.filter(patient_info=patient_info,
                                     uhid_number=uhid_number, is_visible=True).exists():
            raise ValidationError(PatientsConstants.UHID_LINKED_TO_FAMILY_MEMBER)
        uhid_user_info=fetch_uhid_user_details(request)
        uhid_user_info['mobile_verified']=True
        uhid_user_info['is_visible']=True
        if uhid_user_info['email']:
            uhid_user_info['email_verified']=True
        uhid_user_info['patient_info']=patient_info

        self.model.objects.create(**uhid_user_info)

        serializer=self.get_serializer(self.get_queryset(), many=True)

        data={
            "data": serializer.data,
            "message": "New family member is added successfully!"
        }
        link_uhid(request)
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['PATCH'])
    def update_family_member_uhid(self, request, pk=None):
        uhid_number=request.data.get('uhid_number')

        if not uhid_number:
            raise ValidationError(PatientsConstants.ENTER_VALID_UHID)

        patient_info=patient_user_object(request)
        if patient_info.uhid_number == uhid_number:
            raise ValidationError(PatientsConstants.CANT_ASSOCIATE_UHID_TO_FAMILY_MEMBER)

        if self.model.objects.filter(patient_info=patient_info,
                                     uhid_number=uhid_number, is_visible=True).exists():
            raise ValidationError(PatientsConstants.UHID_LINKED_TO_FAMILY_MEMBER)

        uhid_user_info=fetch_uhid_user_details(request)

        family_member=self.get_object()
        family_member.mobile_verified=True
        family_member.first_name=uhid_user_info['first_name']
        family_member.last_name=None
        family_member.middle_name=None
        family_member.mobile=uhid_user_info['mobile']
        if uhid_user_info['email']:
            family_member.email=uhid_user_info['email']
            family_member.email_verified=True
        family_member.gender=uhid_user_info['gender']

        family_member.uhid_number=uhid_number
        family_member.save()

        serializer=self.get_serializer(self.get_queryset(), many=True)
        data={
            "data": serializer.data,
            "message": "Your family member UHID is updated successfully!"
        }
        link_uhid(request)

        return Response(data, status=status.HTTP_200_OK)

    @method_decorator(ratelimit(key=settings.RATELIMIT_KEY_USER_OR_IP, rate=settings.RATELIMIT_OTP_GENERATION, block=True, method=ratelimit.ALL))
    @action(detail=True, methods=['PATCH'])
    def verify_family_member_otp(self, request, pk=None):
        mobile_otp=request.data.get('mobile_otp')
        if not mobile_otp:
            raise ValidationError("Enter OTP to verify family member!")
        try:
            # TODO: self.get_object() doesn't seem to work
            family_member=self.model.objects.get(pk=pk)
        except Exception as error:
            logger.error("Exception in verify_family_member_otp %s"%(str(error)))
            raise NotFound(detail=PatientsConstants.REQUESTED_INFO_NOT_FOUND)

        if not family_member.mobile_verification_otp == mobile_otp:
            raise ValidationError(PatientsConstants.INVALID_OTP)

        if datetime.now().timestamp() > \
                family_member.mobile_otp_expiration_time.timestamp():
            raise OTPExpiredException

        message="Successfull!"

        random_password=get_random_string(
            length=OTP_LENGTH, allowed_chars='0123456789')
        family_member.mobile_verification_otp=random_password

        if family_member.mobile_verified:
            family_member.mobile=family_member.new_mobile
        family_member.mobile_verified=True
        family_member.is_visible=True
        family_member.save()

        serializer=self.get_serializer(self.get_queryset(), many=True)

        data={
            "data": serializer.data,
            "message": message,
        }
        return Response(data, status=status.HTTP_200_OK)

    @method_decorator(ratelimit(key=settings.RATELIMIT_KEY_USER_OR_IP, rate=settings.RATELIMIT_OTP_GENERATION, block=True, method=ratelimit.ALL))
    @action(detail=True, methods=['PATCH'])
    def verify_family_member_email_otp(self, request, pk=None):
        email_otp=request.data.get('email_otp')
        if not email_otp:
            raise ValidationError("Enter OTP to verify family member!")
        try:
            family_member=self.model.objects.get(pk=pk)
        except Exception as error:
            logger.error("Exception in verify_family_member_email_otp %s"%(str(error)))
            raise NotFound(detail=PatientsConstants.REQUESTED_INFO_NOT_FOUND)

        if not family_member.email_verification_otp == email_otp:
            raise ValidationError(PatientsConstants.INVALID_OTP)

        if datetime.now().timestamp() > \
                family_member.email_otp_expiration_time.timestamp():
            raise OTPExpiredException

        random_email_otp=get_random_string(
            length=OTP_LENGTH, allowed_chars='0123456789')
        family_member.email_verification_otp=random_email_otp
        family_member.email_verified=True
        family_member.save()

        serializer=self.get_serializer(self.get_queryset(), many=True)

        data={
            "data": serializer.data,
            "message": "Email is verified successfully!",
        }
        return Response(data, status=status.HTTP_200_OK)

    @method_decorator(ratelimit(key=settings.RATELIMIT_KEY_USER_OR_IP, rate=settings.RATELIMIT_OTP_GENERATION, block=True, method=ratelimit.ALL))
    @action(detail=True, methods=['GET'])
    def generate_family_member_email_verification_otp(self, request, pk=None):
        try:
            family_member_object=self.get_object()
        except Exception as error:
            logger.error("Exception in generate_family_member_email_verification_otp %s"%(str(error)))
            raise NotFound(detail=PatientsConstants.REQUESTED_INFO_NOT_FOUND)

        if family_member_object.email_verified:
            raise ValidationError(PatientsConstants.INVALID_REQUEST)

        random_email_otp=get_random_string(
            length=OTP_LENGTH, allowed_chars='0123456789')
        otp_expiration_time=datetime.now(
        ) + timedelta(seconds=int(settings.OTP_EXPIRATION_TIME))

        send_family_member_email_activation_otp(
            str(family_member_object.id), random_email_otp)

        family_member_object.email_verification_otp=random_email_otp
        family_member_object.email_otp_expiration_time=otp_expiration_time
        family_member_object.save()

        data={
            "data": {"email": str(family_member_object.email)},
            "message": "Please enter OTP which we have sent on your email to activate.",
        }
        return Response(data, status=status.HTTP_200_OK)

    @method_decorator(ratelimit(key=settings.RATELIMIT_KEY_USER_OR_IP, rate=settings.RATELIMIT_OTP_GENERATION, block=True, method=ratelimit.ALL))
    @action(detail=True, methods=['GET'])
    def generate_family_member_mobile_verification_otp(self, request, pk=None):
        try:
            family_member=self.model.objects.get(pk=pk)
        except Exception as error:
            logger.error("Exception in generate_family_member_mobile_verification_otp %s"%(str(error)))
            raise NotFound(detail=PatientsConstants.REQUESTED_INFO_NOT_FOUND)

        if family_member.mobile_verified and not family_member.new_mobile:
            raise ValidationError(PatientsConstants.INVALID_REQUEST)

        mobile_number=str(family_member.mobile.raw_input)
        if family_member.mobile_verified:
            mobile_number=str(family_member.new_mobile.raw_input)

        random_password=get_random_string(
            length=OTP_LENGTH, allowed_chars='0123456789')
        otp_expiration_time=datetime.now(
        ) + timedelta(seconds=int(settings.OTP_EXPIRATION_TIME))

        family_member.mobile_verification_otp=random_password
        family_member.mobile_otp_expiration_time=otp_expiration_time
        family_member.save()

        request_patient=patient_user_object(self.request)

        message="You have been added as a family member on Manipal Hospital application by\
            {}, OTP to activate your account is {}, this OTP will expire in {} seconds".format(
            ValidationUtil.refine_text_only(request_patient.first_name),
            random_password, settings.OTP_EXPIRATION_TIME)

        if self.request.query_params.get('is_android', True):
            message='<#> ' + message + ' ' + settings.ANDROID_SMS_RETRIEVER_API_KEY
        is_message_sent=send_sms(
            mobile_number=mobile_number, message=message)
        if is_message_sent:
            response_message='Please enter OTP which we have sent to your family member.'
        else:
            response_message='We are unable to send OTP to your family member. Please try after sometime.'

        data={
            "data": {"mobile": mobile_number},
            "message": response_message,
        }
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'])
    def add_new_family_member_using_mobile(self, request):
        if self.get_queryset().count() >= int(settings.MAX_FAMILY_MEMBER_COUNT):
            raise ValidationError(PatientsConstants.REACHED_LIMIT_FAMILY_MEMBER)

        uhid_number=request.data.get('uhid_number')
        if not uhid_number:
            raise ValidationError(PatientsConstants.ENTER_VALID_UHID)

        patient_info=patient_user_object(request)
        if patient_info.uhid_number == uhid_number:
            raise ValidationError(PatientsConstants.CANT_ASSOCIATE_UHID_TO_FAMILY_MEMBER)

        if self.model.objects.filter(patient_info=patient_info,
                                     uhid_number=uhid_number, is_visible=True).exists():
            raise ValidationError(PatientsConstants.UHID_LINKED_TO_FAMILY_MEMBER)
                
        uhid_user_info=dict()
        uhid_user_info['first_name'] = request.data.get("first_name")
        uhid_user_info['mobile'] = request.data.get("mobile")
        uhid_user_info['age'] = request.data.get("age")
        uhid_user_info['gender'] = request.data.get("gender")
        
        if request.data.get("email", None):
            uhid_user_info['email'] = request.data.get("email")
            uhid_user_info['email_verified'] = True
        uhid_user_info['uhid_number'] = uhid_number
        uhid_user_info['mobile_verified']=True
        uhid_user_info['is_visible']=True
        uhid_user_info['patient_info']=patient_info

        self.model.objects.create(**uhid_user_info)

        serializer=self.get_serializer(self.get_queryset(), many=True)

        data={
            "data": serializer.data,
            "message": "New family member is added successfully!"
        }
        link_uhid(request)
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['POST'])
    def onboard_family_members(self, request):
        request_data = request.data
        response_data = request_data.get('Data')
        if response_data:
            if self.get_queryset().count() >= int(settings.MAX_FAMILY_MEMBER_COUNT):
                raise ValidationError(PatientsConstants.REACHED_LIMIT_FAMILY_MEMBERS)
                
            for family_member in response_data: 
                uhid_number=family_member.get('uhid_number')
                if not uhid_number:
                    raise ValidationError(PatientsConstants.ENTER_VALID_UHID)

                patient_info=patient_user_object(request)
                if patient_info.uhid_number == uhid_number:
                    raise ValidationError(PatientsConstants.CANT_ASSOCIATE_UHID_TO_FAMILY_MEMBER)

                if self.model.objects.filter(patient_info=patient_info,
                                                uhid_number=uhid_number, is_visible=True).exists():
                    raise ValidationError(PatientsConstants.UHID_LINKED_TO_FAMILY_MEMBER)

                relationship = family_member.get('relationship')
                
                uhid_user_info=dict()
                uhid_user_info['relationship'] = Relation.objects.get(code=relationship)
                uhid_user_info['first_name'] = family_member.get("first_name")
                uhid_user_info['mobile'] = family_member.get("mobile")
                uhid_user_info['age'] = family_member.get("age")
                uhid_user_info['gender'] = family_member.get("gender")
                    
                if family_member.get("email", None):
                    uhid_user_info['email'] = family_member.get("email")
                    uhid_user_info['email_verified'] = False
                uhid_user_info['uhid_number'] = uhid_number
                uhid_user_info['mobile_verified']=True
                uhid_user_info['is_visible']=True
                uhid_user_info['patient_info']=patient_info
                    
                self.model.objects.create(**uhid_user_info)

                serializer=self.get_serializer(self.get_queryset(), many=True)
        else:
            raise ValidationError(PatientsConstants.INVALID_REQUEST)
    
        data={
            "data": serializer.data,
            "message": "New family members is added successfully!"
        }
        link_uhid(request)
        return Response(data, status=status.HTTP_201_CREATED)
      
class PatientAddressViewSet(custom_viewsets.ModelViewSet):
    permission_classes=[IsPatientUser]
    model=PatientAddress
    queryset=PatientAddress.objects.all()
    serializer_class=PatientAddressSerializer
    create_success_message="New address is added successfully."
    list_success_message='Addresses returned successfully!'
    retrieve_success_message='Address information returned successfully!'
    update_success_message='Information is updated successfuly!'
    delete_success_message="Address is deleted successfully"
    filter_backends=(DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    search_fields=['code', 'description', ]
    ordering=('-created_at',)

    def get_permissions(self):
        if self.action in ['list', 'create', 'destroy']:
            permission_classes=[IsPatientUser]
            return [permission() for permission in permission_classes]

        if self.action in ['partial_update', 'retrieve', ]:
            permission_classes=[IsSelfAddress]
            return [permission() for permission in permission_classes]

        if self.action == 'update':
            permission_classes=[BlacklistUpdateMethodPermission]
            return [permission() for permission in permission_classes]

        return super().get_permissions()

    def get_queryset(self):
        return super().get_queryset().filter(patient_info__id=self.request.user.id)

    def perform_create(self, serializer):
        request_data=self.request.data
        longitude=float(request_data.get("longitude", 0))
        latitude=float(request_data.get("latitude", 0))
        serializer.save(location=Point(longitude, latitude, srid=4326))

    def perform_update(self, serializer):
        request_data=self.request.data
        longitude=float(request_data.get("longitude", 0))
        latitude=float(request_data.get("latitude", 0))
        if longitude and latitude:
            serializer.save(location=Point(longitude, latitude, srid=4326))
            return

        serializer.save()


class SendSms(APIView):
    permission_classes=(AllowAny,)

    def post(self, request, format=None):
        encoded_string=request.data.get("checksum")
        mobile=request.data.get("mobile")
        message=request.data.get("message")
        if not (encoded_string and mobile and message):
            raise ValidationError("Invalid Parameter")
        secret_key=settings.SMS_SECRET_KEY
        checksum_string=mobile + secret_key + message
        encoded_string_generated=base64.b64encode(hashlib.sha256(
            checksum_string.encode()).hexdigest().encode()).decode()
        if not (encoded_string == encoded_string_generated):
            raise ValidationError("Invalid Parameter")
        is_message_sent=send_sms(
            mobile_number=str(mobile), message=str(message))
        return Response({"is_message_sent": is_message_sent})


class CovidVaccinationRegistrationView(custom_viewsets.ModelViewSet):
    permission_classes  = [IsPatientUser]
    model               = CovidVaccinationRegistration
    serializer_class    = CovidVaccinationRegistrationSerializer
    queryset            = CovidVaccinationRegistration.objects.all()
    list_success_message        = "Covid vaccination registrations listed successfully"
    retrieve_success_message    = "Covid vaccination registration retrieved successfully"
    create_success_message      = 'Covid vaccination registration completed successfully!'
    update_success_message      = 'Covid vaccination registration updated successfully!'
    delete_success_message      = 'Covid vaccination registration has been deleted successfully!'
    filter_backends = (
                DjangoFilterBackend,
                filters.SearchFilter, 
                filters.OrderingFilter
            )
    filter_fields = ('status', 'registration_no')
    search_fields = ("status","preferred_hospital","patient","family_member","patient__first_name","family_member__first_name" )
    ordering_fields = ('-created_at',)

    def get_queryset(self):
        qs = super().get_queryset()
        admin_object = manipal_admin_object(self.request)
        if admin_object:
            date_from = self.request.query_params.get("date_from", None)
            date_to = self.request.query_params.get("date_to", None)
            if admin_object.hospital:
                qs = qs.filter(preferred_hospital__id=admin_object.hospital.id)
            if date_from and date_to:
                qs = qs.filter(vaccination_date__range=[date_from, date_to])
        else:
            qs = qs.filter(patient__id=self.request.user.id)
        return qs
        

    def get_permissions(self):
        if self.action in ['create', ]:
            permission_classes=[ IsPatientUser ]
            return [permission() for permission in permission_classes]

        if self.action in ['partial_update']:
            permission_classes=[ IsManipalAdminUser ]
            return [permission() for permission in permission_classes]

        if self.action in ['retrieve']:
            permission_classes=[ IsPatientUser | IsManipalAdminUser ]
            return [permission() for permission in permission_classes]

        if self.action == 'list':
            permission_classes=[IsManipalAdminUser | IsPatientUser]
            return [permission() for permission in permission_classes]

        if self.action == 'update':
            permission_classes=[BlacklistUpdateMethodPermission]
            return [permission() for permission in permission_classes]
        
        if self.action == 'destroy':
            permission_classes=[BlacklistDestroyMethodPermission]
            return [permission() for permission in permission_classes]

        return super().get_permissions()

    def create(self, request):
        request_data = request.data.copy()
        covid_registration_mandatory_check(request_data)
        request_data = assign_users(request_data,request.user.id)
        registration_object = self.serializer_class(data = request_data)
        registration_object.is_valid(raise_exception=True)
        registration_object.save()
        return Response(data=registration_object.data,status=status.HTTP_201_CREATED)