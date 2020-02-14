from django.shortcuts import render
import jwt,json
from rest_framework import views
from rest_framework.response import Response
from django.http import HttpResponse
from apps.manipal_admin.models import ManipalAdmin
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from uuid import UUID
from django.contrib.auth.hashers import make_password, check_password
# from django.utils.http import urlsafe_base64_encode
# from django.utils.encoding import force_bytes
# from rest_framework_jwt.utils import jwt_encode_handler, jwt_payload_handler
# Create your views here.
SECRET_KEY = settings.SECRET_KEY

class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return obj.hex
        return json.JSONEncoder.default(self, obj)


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
       if admin:
           payload = {
               'id': admin.id,
               'email': admin.email,
               'password': admin.password,
               'role': admin.role,
               'first_name': admin.first_name,
               'middle_name': admin.middle_name,
               'last_name': admin.last_name
           }
           payload = json.loads(json.dumps(payload, cls = UUIDEncoder))
           jwt_token = {'token': jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')}
           jwt_token['first_name'] = admin.first_name
           jwt_token['middle_name'] = admin.middle_name
           jwt_token['last_name'] = admin.last_name
           jwt_token['role'] = admin.role
           return HttpResponse(
             json.dumps(jwt_token),
             status=200,
             content_type="application/json"
           )


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    data = request.data
    pwd = data.get("password")
    password = make_password(pwd)
    email = data.get("email_id")
    admin = ManipalAdmin.objects.get(email = email)
    if admin:
        admin.password = password
        admin.save()
        return Response({"message": "password set successfully", "status": 200})
    else:
        return Response({"message": "user not found", "status": 400})
