from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import math, random, json
import requests
from datetime import datetime, timedelta, timezone
import boto3
from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response
from apps.users.serializers import UserSerializer
from apps.users.models import BaseUser, Relationship
from rest_framework.parsers import JSONParser
import os
from django.conf import settings

AWS_ACCESS_KEY = settings.AWS_ACCESS_KEY
AWS_SECRET_ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY
REGION_NAME = settings.AWS_SNS_TOPIC_REGION



relationship_CHOICES = {'1': ['Father','2', '4'],
                        '2': ['Son', '1', '3'],
                        '3': ['Mother', '2', '4'],
                        '4': ['Daughter', '1', '3'],
                        '5': ['Brother', '5', '6'],
                        '6': ['Sister', '5', '6'],
                        '7': ['Wife', '8', ''],
                        '8': ['Husband', '', '7'],
                        '9': ['Grand Father', '12', '11'],
                        '10':['Grand Mother', '12', '11'],
                        '11':['Grand Daughter', '9', '10'],
                        '12':['Grand Son', '9', '10'],
                        '13':['Others', '', '']}

def get_reverse_relation(gender, relation):
    if relation == '13':
        return '13'
    if gender == 'Male':
        return relationship_CHOICES.get(relation)[1]
    elif gender == "Female":
        return relationship_CHOICES.get(relation)[1]
    else:
        return '13'

"""
def generate_otp() : 
    digits = "0123456789"
    OTP = ""   
    for i in range(4) : 
        OTP += digits[math.floor(random.random() * 10)]
  
    return OTP
"""



@api_view(['POST'])
def sign_up(request):
    data = request.data
    mobile = data.get("mobile")
    first_name = data.get("first_name")
    last_name  = data.get("last_name")
    gender = data.get("gender")
    facebook_id = data.get("facebook_id")
    google_id = data.get("google_id")
    print("hello")
    mobile_verified = BaseUser.objects.filter(mobile = mobile, mobile_verified =True).first()
    mobile_exist = BaseUser.objects.filter(mobile = mobile).first()
    if mobile_verified :
        return Response({"message": "mobile number already registered", "status": 400})
    else:
        if mobile_exist:
            print("Mobile exist")
            mobile_exist.first_name = first_name
            mobile_exist.last_name = last_name
            mobile_exist.gender = gender
            mobile_exist.facebook_id = facebook_id
            mobile_exist.google_id = google_id
            mobile_exist.save()
        else:
            serializer = UserSerializer(data = data)
            if serializer.is_valid():
                serializer.save()
            else:
                return Response({"message": serializer.errors, "status":400})
        print("OTP is generating")
        message = generate_otp(mobile)
        if(message == 1):
            return Response({"message": "User doesn't exist", "status": 400})
        else:
            return Response({"message": "OTP sent successfully", "status": 200})
            
            

@api_view(['POST'])
def login(request):
    data = request.data
    mobile = data.get("mobile")
    """
    if not "+" in mobile:
        mobile = "+" + mobile
    """
    mobile_exist = BaseUser.objects.filter(mobile = mobile, mobile_verified = True)
    if not mobile_exist:
        return Response({"message": "Mobile number is not registered", "status": 400})
    else:
        message = generate_otp(mobile)
        if(message == 1):
            return Response({"message": "User doesn't exist", "status": 400})
        else:
            return Response({"message": "OTP sent successfully", "status": 200})
        


def generate_otp(mobile, new_mobile = None):
    digits = "0123456789"
    OTP = ""   
    for i in range(4) : 
        OTP += digits[math.floor(random.random() * 10)]
    print(OTP)
    client = boto3.client("sns",
        aws_access_key_id=AWS_ACCESS_KEY, 
        aws_secret_access_key= AWS_SECRET_ACCESS_KEY, 
        region_name= REGION_NAME)  
    response = client.publish(PhoneNumber=mobile, Message = OTP)
    user = BaseUser.objects.filter(mobile = mobile).first()
    if not user:
        return 1
    else:
        user.otp = str(OTP)
        t = datetime.now()
        user.otp_generate_time = t
        user.save()
        return 2


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
    message = generate_otp(mob)
    if(message == 1):
        Response({"message": "User doesn't exist", "status": 400})
    else:
        return Response({"message": "OTP sent successfully", "status": 200})

def family_list(mobile):
    rows =Relationship.objects.filter(relative_user_id__mobile = mobile)
    family_members_details = {}
    family_member = []
    json_obj = {}
    for row in rows:
        json_obj["user_id"] = row.relative_user_id.id
        json_obj["name"] = row.relative_user_id.first_name
        json_obj["relation"] = row.relation
        family_member.append(json_obj)
    json_obj["family_member"] = family_member
    return json_obj



@api_view(['POST'])
def otp_verification(request):
    data = request.data
    mobile = data.get("mobile")
    new_mobile_number = data.get("new_mobile_number")
    google_id = data.get("google_id")
    facebook_id = data.get("facebook_id")
    user_otp = data.get("user_otp")
    mobile_exist = BaseUser.objects.filter(mobile = mobile).first()
    if not mobile_exist:
        return Response({"message": "Please try again", status : 400})
    otp_generate_time = mobile_exist.otp_generate_time
    otp_generate_time.replace(tzinfo=None)
    
    verification_time_limit = otp_generate_time + timedelta(0, 60)
    
    current_time = datetime.now(timezone.utc)
    diff = current_time -verification_time_limit
    
    difference = diff.seconds
    if mobile_exist.otp != user_otp:
        return Response({"message": "OTP is wrong", "status": 400})
    if mobile_exist.otp == user_otp:
        mobile_exist.mobile_verified = True
        mobile_exist.otp = None
        mobile_exist.save()
        if new_mobile_number:
            mobile_exist.mobile = new_mobile_number
            mobile_exist.save()
            return Response({"details": "mobile number changed successfully", "status": 200})
        else:
            mobile_exist = BaseUser.objects.filter(mobile = mobile)
            user_data = mobile_exist.values()[0]
            user_data["family_members"] = list_family_member(mobile)
            return Response({"data": user_data, "message": "mobile number verified", "status": 200})
    """
    if mobile_exist.otp == user_otp and difference > 500:
        return Response({"details": "Time limit exceeds, ask them to resend otp", "status": 400})
    """

@api_view(['POST'])
def facebook_or_google_login(request):
    data = request.data
    facebook_id = data.get("facebook_id")
    if not facebook_id:
        google_id = data.get("google_id")
        if not google_id:
            return Response({"message": "Please send facebook_id or google_id", "status": 402})
    if facebook_id:
        id_exist = BaseUser.objects.filter(facebook_id = facebook_id, mobile_verified = True)
    else:
        id_exist = BaseUser.objects.filter(google_id = google_id,mobile_verified = True)
    if id_exist:
        user = id_exist.values()[0]
        mobile = user.get("mobile")
        message = generate_otp(mobile)
        if(message == 1):
            return Response({"message": "User doesn't exist", "status": 400})
        else:
            return Response({"message": "OTP sent successfully", "status": 200, "mobile": mobile})
    else:
        return Response({"message": "Facebook Id or Google Id Doesn't Exist", "status": 402})


@api_view(['POST'])
def facebook_or_google_signup(request):
    data = request.data
    mobile = data.get("mobile")
    facebook_id = data.get("facebook_id")
    google_id = data.get("google_id")
    mobile_exist = BaseUser.objects.filter(mobile = mobile)
    if mobile_exist:
        user = mobile_exist[0]
        print(user)
        if facebook_id:
            user.facebook_id = facebook_id
        else:
            user.google_id = google_id
            print(user.google_id)
        message = generate_otp(mobile)
        if(message == 1):
            return Response({"message": "User doesn't exist", "status": 400})
        else:
            return Response({"message": "OTP sent successfully", "status": 200})  
    else:
        serializer = UserSerializer(data = data)
        if serializer.is_valid():
            serializer.save()
            message = generate_otp(mobile)
            if(message == 1):
                return Response({"message": "User doesn't exist", "status": 400})
            else:
                return Response({"message": "OTP sent successfully", "status": 200})

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
        return Response({"message": "OTP sent successfully", "status": 200})
    else:
        return Response({"message": "Mobile number is wrong or see your connection", "status": 400})


# @api_view(['POST'])
# def change_mobile_number(request):
#     data = request.data
#     mobile = data.get("mobile")
#     new_mobile_number = data.get("new_mobile_number")
#     mobile_exist = BaseUser.objects.filter(mobile = new_mobile_number)
#     if mobile_exist:
#         return Response({"details": "Mobile number is already registred", "status": 400})
#     res = requests.get("http://localhost:8000/api/user/send_otp/", params = {"new_mobile_number": new_mobile_number, "mobile": mobile})
#     if res.status_code == 200:
#         return Response({"details": "OTP sent successfully", "status": 200})
#     else:
#         return Response({"details": "Mobile number is wrong or see your connection", "status": 400})


@api_view(['POST'])
def set_gender(request):
    data = request.data
    mobile = data.get("mobile")
    gender = data.get("gender")
    user = BaseUser.objects.get(mobile = mobile)
    if user:
        user.gender = gender
        user.save()
        return Response({"message": "gender set successfully", "status": 200})
    else:
        return Response({"message": "user not found", "status": 400})

@api_view(['POST'])
def add_family_member(request):
    data = request.data
    mobile = data.get("mobile")
    relation = data.get("relation")
    user = BaseUser.objects.filter(mobile = mobile).first()
    if not user:
        return Response({"message": "User doesn't Exist", "status": 400})
    """
    user_gender = user.gender
    if not user_gender:
        return Response({"details": "user gender not found", "status": 200})
    """
    family_member_mobile = data.get("family_member_mobile")
    mobile_verified = BaseUser.objects.filter(mobile = family_member_mobile, mobile_verified = True)
    if mobile_verified:
        return Response({"details": "family member already exist", "status": 400})
    else:
        BaseUser.objects.filter(mobile = family_member_mobile).delete()
        data['mobile'] = family_member_mobile
        serializer = UserSerializer(data = data)
        if serializer.is_valid():
            serializer.save()
            message = generate_otp(family_member_mobile)
            if(message == 1):
                return Response({"message": "User doesn't exist", "status": 400})
            else:
                return Response({"message": "OTP sent successfully", "status": 200})       
        else:
            return Response({"message": serializer.errors, "status":400})

@api_view(['POST'])
def add_family_member_verification(request):
    data = request.data
    mobile = data.get("mobile")
    relation = data.get("relation")
    family_member_mobile = data.get("family_member_mobile")
    user_otp = data.get("user_otp")
    user = BaseUser.objects.get(mobile = mobile)
    mobile_exist = BaseUser.objects.filter(mobile = family_member_mobile).first()
    otp_generate_time = mobile_exist.otp_generate_time
    otp_generate_time.replace(tzinfo=None)
    verification_time_limit = otp_generate_time + timedelta(0, 60)
    current_time = datetime.now(timezone.utc)
    diff = current_time -verification_time_limit
    difference = diff.seconds
    if mobile_exist.otp != user_otp:
        return Response({"message": "OTP is wrong", "status": 400})
    else:
        mobile_exist.mobile_verified = True
        mobile_exist.otp = None
        mobile_exist.save()
        relationship_exist = Relationship.objects.filter(user_id = user, relative_user_id = mobile_exist).first()
        if relationship_exist:
            return Response({"message": "Member is already part of your family", "status":400})
        R1 = Relationship(relation = relation, user_id = user, relative_user_id = mobile_exist)
        R1.save()
        print("object is saved")
        family_list = list_family_member(mobile)
        user_data = BaseUser.objects.filter(mobile = mobile).values()[0]
        user_data["family_members"] = family_list
        return Response({"data": user_data,"message": "Member has been added", "status": 200})




@api_view(['POST'])
def edit_family_member(request):
    data = request.data
    mobile = data.get("mobile")
    family_member_mobile = data.get("family_member_mobile")
    family_user = BaseUser.objects.filter(mobile = family_member_mobile).first()
    """
    serializer = UserSerializer(family_user, data=data, partial=True)
    if serializer.is_valid():
        serializer.save()
    """
    family_user.first_name = data.get("first_name")
    family_user.last_name = data.get("last_name")
    family_user.gender = data.get("gender")
    family_user.save()
    relation = Relationship.objects.filter(user_id_id__mobile= mobile,relative_user_id_id__mobile = family_member_mobile).first()
    relation.relation = data.get("relation")
    relation.save()
    user_data = BaseUser.objects.filter(mobile = mobile).values()[0]
    
    user_data["family_members"] = list_family_member(mobile)
    return Response({"data": user_data,"message": "Profile is updated", "status": 200})


@api_view(['POST'])
def delete_family_member(request):
    data = request.data
    mobile = data.get("mobile")
    family_member_mobile = data.get("family_member_mobile")
    """
    family_user = BaseUser.objects.get(mobile = family_member_mobile)
    idd = family_user.id
    """
    Relationship.objects.filter(user_id_id__mobile = mobile, relative_user_id_id__mobile = family_member_mobile).delete()
    user_data = BaseUser.objects.filter(mobile = mobile).values()[0]
    user_data["family_members"] = list_family_member(mobile)
    return Response({"data": user_data,"message": "succesfully deleted", "status": 200})
    


def list_family_member(mobile):
    rows =Relationship.objects.filter(user_id_id__mobile = mobile)
    family_members_details = {}
    family_member = []
    for row in rows:
        json_obj = {}
        json_obj["first_name"] = row.relative_user_id.first_name
        json_obj["relation"] = row.relation
        json_obj["mobile"] = str(row.relative_user_id.mobile)
        json_obj["last_name"] = row.relative_user_id.last_name
        json_obj["gender"] = row.relative_user_id.gender
        json_obj["UHID"] = ""
        family_member.append(json_obj.copy())
    return family_member
        
    """
        family_member = BaseUser.objects.filter(id = rel_idd).values()[0]
        family_member_details["family_member"] = family_member
        family_member_details["relation"] = relation
        family_members_details.append(family_member_details)
    """


@api_view(['POST'])
def set_favorite_hospital(request):
    data = request.data
    code = data.get("favorite_hospital_code")
    mobile = data.get("mobile")
    user = BaseUser.objects.get(mobile = mobile)
    user.favorite_hospital_code = code
    user.save()
    return Response({"details": "Favorite Hospital Saved", "status": 200})

@api_view(['POST'])
def list_family_members(request):
    data = request.data
    mobile = data.get("mobile")
    rows =Relationship.objects.filter(user_id_id__mobile = mobile)
    family_members = []
    family_member = []
    
    for row in rows:
        json_obj = {}
        json_obj["first_name"] = row.relative_user_id.first_name
        json_obj["relation"] = row.relation
        json_obj["mobile"] = str(row.relative_user_id.mobile)
        json_obj["last_name"] = row.relative_user_id.last_name
        json_obj["UHID"] = ""
        family_member.append(json_obj.copy())
    return Response({"data": family_member})
        
    """
        family_member = BaseUser.objects.filter(id = rel_idd).values()[0]
        family_member_details["family_member"] = family_member
        family_member_details["relation"] = relation
        family_members_details.append(family_member_details)
    """
