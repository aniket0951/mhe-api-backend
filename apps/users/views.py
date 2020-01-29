from django.shortcuts import render
import math, random
import requests
from datetime import datetime, timedelta, timezone
import boto3
from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response
from apps.users.serializers import UserSerializer
from apps.users.models import BaseUser
from rest_framework.parsers import JSONParser

# @api_view(['GET'])
# def base(request):
#     return render(request, "question_answer/base.html")

ACCESS_KEY = "AKIA42WKBMR76XEKBBVR"
SECRET_KEY  = "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"
SNS_TOPIC_NAME = "mhe-dev"
SNS_TOPIC_REGION = "ap-southeast-1"
SNS_Topic_ARN  = "arn:aws:sns:ap-southeast-1:881965753471:mhe-dev"

def generate_otp() : 
    digits = "0123456789"
    OTP = ""   
    for i in range(4) : 
        OTP += digits[math.floor(random.random() * 10)] 
  
    return OTP


@api_view(['POST'])
def sign_up(request):
    data = request.data
    mobile = data.get("mobile")
    mobile_exist = BaseUser.objects.filter(mobile = mobile)
    if mobile_exist:
        return Response({"details": "mobile number already registered", "status": 400})
    serializer = UserSerializer(data = data)
    if serializer.is_valid():
        serializer.save()
        return Response("1234", status=200)


@api_view(['GET'])
def send_otp(request):
    data = request.query_params
    mobile = data.get("mobile")
    new_mobile_number = data.get("new_mobile_number")
    if new_mobile_number:
        mob = new_mobile_number
    else:
        mob = mobile
    if not "+" in mob:
        mob = "+" + str(mob)
    otp = generate_otp()
    client = boto3.client("sns",
        aws_access_key_id="AKIA42WKBMR76XEKBBVR", 
        aws_secret_access_key="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", 
        region_name="ap-southeast-1")
    response = client.publish(PhoneNumber=mob, Message = otp)
    user = BaseUser.objects.get(mobile = mobile)
    user.otp = str(otp)
    t = datetime.now()
    user.otp_generate_time = t
    user.save()
    return Response({"details": "OTP sent successfully", "status": 200})


@api_view(['POST'])
def otp_verification(request):
    data = request.data
    mobile = data.get("mobile")
    new_mobile_number = data.get("new_mobile_number")
    user_otp = data.get("user_otp")
    mobile_exist = BaseUser.objects.get(mobile = mobile)
    otp_generate_time = mobile_exist.otp_generate_time
    otp_generate_time.replace(tzinfo=None)
    verification_time_limit = otp_generate_time + timedelta(0, 60)

    current_time = datetime.now(timezone.utc)
    diff = current_time -verification_time_limit
    difference = diff.seconds
    if mobile_exist.otp != user_otp:
        return Response({"details": "OTP is wrong", "status": 400})
    if mobile_exist.otp == user_otp and difference < 60:
        if new_mobile_number:
            mobile_exist.mobile = new_mobile_number
        mobile_exist.mobile_verified = True
        mobile_exist.save()
        return Response({"details": "mobile number verified", "status": 200})
    if mobile_exist.otp == user_otp and difference > 60:
        return Response({"details": "Time limit exceeds, ask them to resend otp", "status": 400})


@api_view(['GET'])
def login(request):
    data = request.data
    mobile = data.get("mobile")
    mobile_exist = BaseUser.objects.filter(mobile = mobile)
    if mobile_exist:
        res = requests.get("http://localhost:8000/api/user/send_otp/", params = {"mobile": mobile})
        if res.status_code == 200:
            return Response({"details": "OTP sent successfully", "status": 200})
    else:
        return Response({"details": "Mobile number is not registred", "status": 400})


@api_view(['POST'])
def facebook_or_google_login(request):
    data = request.data
    facebook_id = data.get("facebook_id")
    if not facebook_id:
        google_id = data.get("google_id")
        if not google_id:
            return Response({"details": "Please send facebook_id or google_id", "status": 500})
    if facebook_id:
        id_exist = BaseUser.objects.filter(facebook_id = facebook_id)
    else:
        id_exist = BaseUser.objects.filter(facebook_id = google_id)
    if id_exist:
        user = id_exist.values()[0]
        mobile = user.get("mobile")
        res = requests.get("http://localhost:8000/api/user/send_otp/", params = {"mobile": mobile})
        if res.status_code == 200:
            return Response({"details": "OTP sent successfully", "status": 200})
    else:
        return Response({"details": "facebook_id or google_id not found, please share name and mobile number", "status": 400})


@api_view(['POST'])
def facebook_or_google_signup(request):
    data = request.data
    mobile = data.get("mobile")
    facebook_id = data.get("facebook_id")
    google_id = data.get("google_id")
    mobile_exist = BaseUser.objects.filter(mobile = mobile)
    if mobile_exist:
        user = mobile_exist.values()
        if facebook_id:
            user.update(facebook_id = facebook_id)
        else:
            user.update(google_id = google_id)
        res = requests.get("http://localhost:8000/api/user/send_otp/", params = {"mobile": mobile})
        if res.status_code == 200:
            return Response({"details": "OTP sent successfully", "status": 200})
    
    else:
        serializer = UserSerializer(data = data)
        if serializer.is_valid():
            serializer.save()
            res = requests.get("http://localhost:8000/api/user/send_otp/", params = {"mobile": mobile})
            if res.status_code == 200:
                return Response({"details": "OTP sent successfully", "status": 200})


@api_view(['POST'])
def change_mobile_number(request):
    data = request.data
    mobile = data.get("mobile")
    new_mobile_number = data.get("new_mobile_number")
    mobile_exist = BaseUser.objects.filter(mobile = new_mobile_number)
    if mobile_exist:
        return Response({"details": "Mobile number is already registred", "status": 400})
    res = requests.get("http://localhost:8000/api/user/send_otp/", params = {"new_mobile_number": new_mobile_number, "mobile": mobile})
    if res.status_code == 200:
        return Response({"details": "OTP sent successfully", "status": 200})
    else:
        return Response({"details": "Mobile number is wrong or see your connection", "status": 400})


# @api_view(['GET'])
# def set_favorite_hospital(request):
#     data = request.query_params
#     code = data.get("favorite_hospital_code")
#     new_mobile_number = data.get("new_mobile_number")
#     mobile_exist = BaseUser.objects.filter(mobile = new_mobile_number)
#     if mobile_exist:
#         return Response({"details": "Mobile number is already registred", "status": 400})
#     res = requests.get("http://localhost:8000/api/user/send_otp/", params = {"new_mobile_number": new_mobile_number, "mobile": mobile})
#     if res.status_code == 200:
#         return Response({"details": "OTP sent successfully", "status": 200})
#     else:
#         return Response({"details": "Mobile number is wrong or see your connection", "status": 400})


# Create your views here.
