import json
from uuid import UUID
from django.conf import settings
from rest_framework.response import Response
from django.http import HttpResponse
from django.contrib.auth.hashers import check_password
from rest_framework_jwt.utils import jwt_encode_handler
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes

from apps.manipal_admin.models import ManipalAdmin

# Create your views here.

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
           jwt_token = {"token": jwt_encode_handler(payload)}
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