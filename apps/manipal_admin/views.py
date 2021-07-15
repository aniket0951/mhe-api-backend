from django.db.models.query_utils import Q
from apps.patients.models import Patient
import json
from datetime import datetime

from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.contrib.auth.tokens import default_token_generator
from django.core import serializers
from django.http import HttpResponse
from django.utils.http import urlsafe_base64_decode
from rest_framework import filters, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework_jwt.utils import jwt_encode_handler, jwt_payload_handler

from apps.manipal_admin.models import ManipalAdmin, AdminMenu, AdminRole
from apps.manipal_admin.serializers import ManipalAdminSerializer
from apps.patients.exceptions import InvalidCredentialsException
from utils.custom_permissions import IsManipalAdminUser, IsPlatformAdmin
from utils.utils import manipal_admin_object
from utils.custom_jwt_whitelisted_tokens import WhiteListedJWTTokenUtil
from utils.custom_jwt_authentication import JSONWebTokenAuthentication
from .emails import send_reset_password_email
from .exceptions import (
                    ManipalAdminDoesNotExistsValidationException,
                    ManipalAdminPasswordURLExipirationValidationException,
                    ManipalAdminPasswordURLValidationException,
                    ManipalAdminDisabledUserException
                )
from .serializers import ManipalAdminResetPasswordSerializer, ManipalAdminMenuSerializer, ManipalAdminRoleSerializer, ManipalAdminTypeSerializer
from utils import custom_viewsets
from django_filters.rest_framework import DjangoFilterBackend

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    email = request.data.get('email_id')
    password = request.data.get('password')
    if not (email and password):
        raise InvalidCredentialsException

    admin = ManipalAdmin.objects.filter(email=email).first()
    if not admin:
        raise ManipalAdminDoesNotExistsValidationException
    
    hash_password = admin.password
    match_password = check_password(password, hash_password)
    if not match_password:
        raise InvalidCredentialsException

    if not admin.is_active:
        raise ManipalAdminDisabledUserException
    
    payload = jwt_payload_handler(admin)
    payload['mobile'] = payload['mobile'].raw_input
    payload['username'] = payload['username'].raw_input
    token = jwt_encode_handler(payload)
    expiration = datetime.utcnow() + settings.JWT_AUTH['JWT_EXPIRATION_DELTA']
    expiration_epoch = expiration.timestamp()

    WhiteListedJWTTokenUtil.create_token(admin,token)

    serializer = ManipalAdminSerializer(admin)
    data = {
        "data": serializer.data,
        "message":  "Login successful!",
        "token": token,
        "token_expiration": expiration_epoch
    }
    return Response(data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def logout(request):
    JSONWebTokenAuthentication().logout_user(request)
    data = {
        "message":  "Logout successful!"
    }
    return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    email = request.data.get('email_id')
    if not email:
        raise ValidationError("Email ID not provided!")

    admin = ManipalAdmin.objects.filter(email=email).first()
    if not admin:
        raise ManipalAdminDoesNotExistsValidationException

    send_reset_password_email(request, admin.id)

    data = {
        'data': None,
        'message': 'Please follow the instructions mentioned in the email to reset your password.'
    }
    return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsManipalAdminUser])
def change_password(request):
    password = request.data.get("password")
    new_password = request.data.get("new_password")
    if not (password and new_password):
        raise ValidationError(
            "Inavlid request, enter your current and new password.")

    admin = manipal_admin_object(request)
    hash_password = admin.password
    match_password = check_password(password, hash_password)
    if not match_password:
        raise InvalidCredentialsException

    admin.set_password(new_password)
    admin.save()
    data = {
        "data": None,
        "message":  "Successfully changed your password!",
    }
    return Response(data, status=status.HTTP_200_OK)


class ManipalAdminResetPasswordView(CreateAPIView):
    permission_classes = [AllowAny]
    model = ManipalAdmin
    message = 'Password has been reset successfully.'
    serializer_class = ManipalAdminResetPasswordSerializer

    def post(self, request, uidb64=None, token=None):
        assert uidb64 is not None and token is not None  # checked by URLconf
        try:
            uid = urlsafe_base64_decode(uidb64).decode("utf-8")
            user = self.model._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, ManipalAdmin.DoesNotExist):
            raise ManipalAdminPasswordURLValidationException

        if not default_token_generator.check_token(user, token):
            raise ManipalAdminPasswordURLExipirationValidationException

        if not request.data['password']:
            raise ValidationError('Password is not provided!')

        new_password = request.data['password']
        user.set_password(new_password)
        user.save()

        context = {'data': None, 'message': self.message}
        return Response(context, status=status.HTTP_200_OK)

class AdminMenuView(custom_viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsPlatformAdmin]
    model = AdminMenu
    serializer_class = ManipalAdminMenuSerializer
    queryset = AdminMenu.objects.all()
    list_success_message = "Admin menus listed successfully"
    retrieve_success_message = "Admin menus retrieved successfully"

    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    search_fields = ['name', ]
    ordering_fields = ('-created_at',)
    pagination_class = None

class AdminRoleView(custom_viewsets.ModelViewSet):
    permission_classes = [IsPlatformAdmin]
    model = AdminRole
    serializer_class = ManipalAdminRoleSerializer
    queryset = AdminRole.objects.all()
    list_success_message = "Admin roles listed successfully"
    retrieve_success_message = "Admin role retrieved successfully"
    create_success_message = 'Role creation completed successfully!'
    update_success_message = 'Information updated successfully!'
    delete_success_message = 'Role has been deleted successfully!'

    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    search_fields = ['name', ]
    ordering_fields = ('-created_at',)

    def create(self, request):
        admin_menu_object = self.serializer_class(data = request.data)
        admin_menu_object.is_valid()
        admin_menu_object.save()
        return Response(status=status.HTTP_200_OK)
    
class ManipalAdminView(custom_viewsets.ModelViewSet):
    permission_classes = [IsPlatformAdmin]
    model = ManipalAdmin
    serializer_class = ManipalAdminTypeSerializer
    queryset = ManipalAdmin.objects.all()
    list_success_message = "Admin roles listed successfully"
    retrieve_success_message = "Admin role retrieved successfully"
    create_success_message = 'Role creation completed successfully!'
    update_success_message = 'Information updated successfully!'
    delete_success_message = 'Role has been deleted successfully!'

    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    search_fields = ['name', ]
    ordering_fields = ('-created_at',)

    def create(self, request):
        mobile = request.data.get('mobile')
        email = request.data.get("email")
        if not mobile:
            raise ValidationError("Mobile is mandatory")
        if not email:
            raise ValidationError("Email is mandatory")
        if Patient.objects.filter(Q(mobile=mobile)|Q(email=email)).exists():
            raise ValidationError("Patient with the same mobile number or email id already exists!")
        request.data['is_active'] = True
        admin_object = self.serializer_class(data = request.data)
        admin_object.is_valid(raise_exception=True)
        admin_object.save()
        if request.data.get('password'):
            user_object = ManipalAdmin.objects.filter(email=email).first()
            user_object.set_password(request.data.get('password'))
            user_object.save()
        return Response(status=status.HTTP_200_OK)
    
        

    

    
    
    