import json
from django.conf import settings
from rest_framework.response import Response
from django.http import HttpResponse
from django.core import serializers
from django.contrib.auth.hashers import check_password
from rest_framework_jwt.utils import jwt_encode_handler, jwt_payload_handler
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes

from apps.manipal_admin.models import ManipalAdmin
from apps.manipal_admin.serializers import AdminSerializer

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
       jwt_token = jwt_encode_handler(payload)
       admin_data = AdminSerializer([admin], many = True)
       response = {}
       response["admin_data"] = admin_data.data
       response['token'] = jwt_token
       return Response({"data": response, "message": "logged in successfully", "status": 200})


@api_view(['POST'])
@permission_classes([AllowAny])
def change_password(request):
    data = request.data
    password = data.get("password")
    email = data.get("email_id")
    try:
        admin = ManipalAdmin.objects.get(email = email)
    except Exception as e:
        return Response({"message": "given email id is not found", "status": 400})
    if admin:
        admin.set_password(password)
        admin.save()
        return Response({"message": "password set successfully", "status": 200})