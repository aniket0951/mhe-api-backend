from datetime import datetime, timedelta
from rest_framework.permissions import AllowAny
from rest_framework_jwt.utils import jwt_encode_handler, jwt_payload_handler
from apps.patients.exceptions import OTPExpiredException
from apps.patients.models import OtpGenerationCount
from apps.patients.utils import check_max_otp_retries, save_authentication_type, validate_access_attempts
from apps.phlebo.models import Phlebo
from apps.phlebo.serializers import PhleboSerializer
from utils import custom_viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.serializers import ValidationError
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from ratelimit.decorators import ratelimit

from django.conf import settings
from django.contrib.auth.models import update_last_login
from django.contrib.gis.geos import Point
from django.utils.crypto import get_random_string
from rest_framework.decorators import action
from utils.custom_sms import send_sms
from utils.custom_jwt_whitelisted_tokens import WhiteListedJWTTokenUtil

OTP_LENGTH = settings.OTP_LENGTH

class PhleboAPIView(custom_viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    model = Phlebo
    queryset = Phlebo.objects.all()
    serializer_class = PhleboSerializer
    
    create_success_message = 'Phlebo registered successfully!'
    update_success_message = 'Phlebo information updated successfully!'
    list_success_message = "Phlebo information returned successfully"
    retrieve_success_message = "Phlebo information retrieved successfully"

    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    ordering_fields = ('-created_at',)

    # def create(self, request):
    #     mobile = request.data.get('mobile')
    #     email = request.data.get("email")
    #     if not mobile:
    #         raise ValidationError("Mobile is mandatory")
    #     if not email:
    #         raise ValidationError("Email is mandatory")
      
    #     request.data['is_active'] = True
    #     admin_object = self.serializer_class(data = request.data)
    #     admin_object.is_valid(raise_exception=True)
    #     admin_object.save()
    #     if request.data.get('password'):
    #         user_object = Phlebo.objects.filter(email=email).first()
    #         user_object.set_password(request.data.get('password'))
    #         user_object.save()
    #     return Response(status=status.HTTP_200_OK)
    
    def perform_create(self, serializer):

                
        phlebo_obj = self.get_queryset().filter(
            mobile=self.request.data.get('mobile')).first()

        random_password = get_random_string(length=OTP_LENGTH, allowed_chars='0123456789')
        otp_expiration_time = datetime.now() + timedelta(seconds=int(settings.OTP_EXPIRATION_TIME))

        if phlebo_obj:
            phlebo_obj.set_password(random_password)
            phlebo_obj.otp_expiration_time = otp_expiration_time
            phlebo_obj.save()
            self.serializer = self.get_serializer(phlebo_obj)
            user_obj = phlebo_obj

        else:
            user_obj = serializer.save(
                otp_expiration_time=otp_expiration_time,
                is_active=True)

            user_obj.set_password(random_password)
            user_obj.save()

        check_max_otp_retries(user_obj)

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
    
    @method_decorator(ratelimit(key=settings.RATELIMIT_KEY_IP, rate=settings.RATELIMIT_OTP_GENERATION, block=True, method=ratelimit.ALL))
    @action(detail=False, methods=['POST'])
    def generate_login_otp(self, request):

        mobile = request.data.get('mobile')
        
        request_patient = self.validate_request_data_for_generate_login_otp(mobile)    

        random_password = get_random_string(
            length=OTP_LENGTH, allowed_chars='0123456789')

        otp_expiration_time = datetime.now() + timedelta(seconds=int(settings.OTP_EXPIRATION_TIME))

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
    
    @method_decorator(ratelimit(key=settings.RATELIMIT_KEY_IP, rate=settings.RATELIMIT_OTP_GENERATION, block=True, method=ratelimit.ALL))
    @action(detail=False, methods=['POST'])
    def verify_login_otp(self, request):
        username = request.data.get('mobile')
        password = request.data.get('password') or request.data.get('otp')
        email = self.request.data.get("email")

        authenticated_user = validate_access_attempts(username,password,request)

        if datetime.now().timestamp() > authenticated_user.otp_expiration_time.timestamp():
            raise OTPExpiredException
        message = "Login successful!"

        save_authentication_type(authenticated_user,email)

        update_last_login(None, authenticated_user)
        if not authenticated_user.mobile_verified:
            authenticated_user.mobile_verified = True
            message = "Your account is activated successfully!"
        random_password = get_random_string(
            length=OTP_LENGTH, allowed_chars='0123456789')
        authenticated_user.set_password(random_password)
        authenticated_user.save()
        
        serializer = self.get_serializer(authenticated_user)
        payload = jwt_payload_handler(authenticated_user)
        payload['username'] = payload['username'].raw_input
        payload['mobile'] = payload['mobile'].raw_input
        token = jwt_encode_handler(payload)
        expiration = datetime.utcnow() + settings.JWT_AUTH['JWT_EXPIRATION_DELTA']
        expiration_epoch = expiration.timestamp()

        otp_instance = OtpGenerationCount.objects.filter(mobile=authenticated_user.mobile).first()
        if otp_instance:
            otp_instance.otp_generation_count = 0
            otp_instance.save()

        WhiteListedJWTTokenUtil.create_token(authenticated_user,token)

        data = {
            "data": serializer.data,
            "message": message,
            "token": token,
            "token_expiration": expiration_epoch
        }
        return Response(data, status=status.HTTP_200_OK)
    