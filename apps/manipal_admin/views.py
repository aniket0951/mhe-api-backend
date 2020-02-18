import json

from apps.manipal_admin.models import ManipalAdmin
from apps.manipal_admin.serializers import AdminSerializer
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.core import serializers
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_jwt.utils import jwt_encode_handler, jwt_payload_handler


# Create your views here.


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    if not request.data:
        return Response({'message': "Please provide username/password"}, status="400")
    email = request.data.get('email_id')
    password = request.data.get('password')
    try:
        admin = ManipalAdmin.objects.get(email=email)
        hash_password = admin.password
        match_password = check_password(password, hash_password)
        if not match_password:
            raise Exception
    except Exception as e:
        return Response({'message': "Invalid username/password"}, status="400")

    payload = jwt_payload_handler(admin)
    payload['mobile'] = payload['mobile'].raw_input
    payload['username'] = payload['username'].raw_input
    jwt_token = jwt_encode_handler(payload)
    data = AdminSerializer(admin)
    admin_data = data.data
    return Response({"data": admin_data, "token": jwt_token, "message": "Successfully logged in.", "status": 200})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    data = request.data
    password = data.get("password")
    email = data.get("email_id")
    new_password = data.get("new_password")
    try:
        admin = ManipalAdmin.objects.get(email=email)
        hash_password = admin.password
        match_password = check_password(password, hash_password)
        if not match_password:
            return Response({"message": "Current password didn't match.", "status": 400})
        admin.set_password(new_password)
        admin.save()
        return Response({"message": "Successfully changed password.", "status": 200})
    except Exception as e:
        return Response({"message": "Email id is incorrect.", "status": 400})
