import json
from datetime import datetime

from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.core import serializers
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework_jwt.utils import jwt_encode_handler, jwt_payload_handler

from apps.manipal_admin.models import ManipalAdmin
from apps.manipal_admin.serializers import ManipalAdminSerializer
from apps.patients.exceptions import InvalidCredentialsException
from manipal_api.settings import JWT_AUTH
from utils.custom_permissions import IsManipalAdminUser
from utils.utils import manipal_admin_object

from .exceptions import ManipalAdminDoesNotExistsValidationException

# Create your views here.


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
    payload = jwt_payload_handler(admin)
    payload['mobile'] = payload['mobile'].raw_input
    payload['username'] = payload['username'].raw_input
    token = jwt_encode_handler(payload)
    expiration = datetime.utcnow(
        ) + JWT_AUTH['JWT_EXPIRATION_DELTA']
    expiration_epoch = expiration.timestamp()
    serializer = ManipalAdminSerializer(admin)
    data = {
        "data": serializer.data,
        "message":  "Login successful!",
        "token": token,
        "token_expiration": expiration_epoch
    }
    return Response(data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsManipalAdminUser])
def change_password(request):
    password = request.data.get("password")
    new_password = request.data.get("new_password")
    if not (password and new_password):
        raise ValidationError("Inavlid request, enter your current and new password.")

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
