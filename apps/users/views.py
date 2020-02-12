from django.shortcuts import render
import urllib
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
import threading
from boto3.s3.transfer import TransferConfig

AWS_ACCESS_KEY = settings.AWS_ACCESS_KEY
AWS_SECRET_ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY
REGION_NAME = settings.AWS_SNS_TOPIC_REGION
S3_BUCKET_NAME = settings.AWS_S3_BUCKET_NAME
S3_REGION_NAME = settings.AWS_S3_REGION_NAME


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
def edit_user_profile(request):
    data = request.data
    user_id = data.get("user_id")
    first_name = data.get("first_name")
    last_name  = data.get("last_name")
    gender = data.get("gender")
    email = data.get("email")

    mobile_verified = BaseUser.objects.filter(id = user_id, mobile_verified =True).first()
    if mobile_verified:
        mobile_verified.first_name = first_name
        mobile_verified.last_name = last_name
        mobile_verified.gender = gender
        mobile_verified.email = email
        mobile_verified.save()
        family_list = list_family_member(mobile_verified.id)
        user_data = BaseUser.objects.filter(id = user_id).values()[0]
        user_data["family_members"] = family_list
        return Response({"data": user_data, "message": "User Profile has been updated", "status": 200})
    else:
        return Response({"message": "User doesn't Exist", "status": 400})




@api_view(['POST'])
def sign_up(request):
    data = request.data
    mobile = data.get("mobile")
    first_name = data.get("first_name")
    last_name  = data.get("last_name")
    gender = data.get("gender")
    facebook_id = data.get("facebook_id")
    google_id = data.get("google_id")
    mobile_verified = BaseUser.objects.filter(mobile = mobile, mobile_verified =True).first()
    mobile_exist = BaseUser.objects.filter(mobile = mobile).first()
    
    if mobile_verified :
        if google_id or facebook_id:
            if google_id:
                mobile_verified.google_id = google_id
            else:
                mobile_verified.facebook_id = facebook_id
            mobile_verified.save()
            message , OTP = generate_otp(mobile_verified.id, str(mobile_verified.mobile))
            if(message == 1):
                return Response({"message": "User doesn't exist", "status": 400})
            else:
                return Response({"message": "OTP sent successfully", "status": 200, "OTP": OTP, "id": mobile_verified.id })
        else:
            return Response({"message": "mobile number already registered", "status": 400})
    else:
        message = ""
        OTP = ""
        if mobile_exist:
            mobile_exist.first_name = first_name
            mobile_exist.last_name = last_name
            mobile_exist.gender = gender
            mobile_exist.facebook_id = facebook_id
            mobile_exist.google_id = google_id
            mobile_exist.save()
            message , OTP = generate_otp(mobile_exist.id, str(mobile_exist.mobile))
            return Response({"message": "OTP sent successfully", "status": 200, "OTP": OTP, "id": mobile_exist.id })
        else:
            serializer = UserSerializer(data = data)
            if serializer.is_valid():
                mobile_new = serializer.save()
                message , OTP = generate_otp(mobile_new.id, str(mobile_new.mobile))
                return Response({"message": "OTP sent successfully", "status": 200, "OTP": OTP, "id": mobile_new.id })
            else:
                return Response({"message": serializer.errors, "status":400})
            
            

@api_view(['POST'])
def login(request):
    data = request.data
    mobile = data.get("mobile")
    mobile_exist = BaseUser.objects.filter(mobile = mobile, mobile_verified = True).first()
    print(mobile_exist)
    if not mobile_exist:
        return Response({"message": "Mobile number is not registered", "status": 400})
    else:
        message, OTP = generate_otp(mobile_exist.id, str(mobile_exist.mobile))
        if(message == 1):
            return Response({"message": "User doesn't exist", "status": 400})
        else:
            return Response({"message": "OTP sent successfully", "status": 200, "OTP":OTP, "id":mobile_exist.id})
        


def generate_otp(user_id, mobile):
    digits = "0123456789"
    OTP = ""   
    for i in range(4) : 
        OTP += digits[math.floor(random.random() * 10)]
    print(OTP)
    """
    client = boto3.client("sns",
        aws_access_key_id=AWS_ACCESS_KEY, 
        aws_secret_access_key= AWS_SECRET_ACCESS_KEY, 
        region_name= REGION_NAME)  
    response = client.publish(PhoneNumber=mobile, Message = OTP, MessageAttributes = {
                   'AWS.SNS.SMS.SMSType': {
                       'DataType': 'String',
                       'StringValue': 'Transactional'
                   }
    })
    """
    user = BaseUser.objects.filter(id = user_id).first()
    if not user:
        return 1, OTP 
    else:
        user.otp = str(OTP)
        t = datetime.now()
        user.otp_generate_time = t
        user.save()
        return 2, OTP


@api_view(['GET'])
def send_otp(request):
    data = request.query_params
    user_id = data.get("user_id")
    user = BaseUser.objects.filter(id = user_id).first()
    message, OTP = generate_otp(user.id, str(user.mobile))
    if(message == 1):
        return Response({"message": "User doesn't exist", "status": 400})
    else:
        return Response({"message": "OTP sent successfully", "status": 200, "OTP":OTP, "id": user.id, "mobile":str(user.mobile)})

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
    user_id = data.get("user_id")
    google_id = data.get("google_id")
    facebook_id = data.get("facebook_id")
    user_otp = data.get("user_otp")
    mobile_exist = BaseUser.objects.filter(id = user_id).first()
    if not mobile_exist:
        return Response({"message": "Please try again", "status" : 400})
    if (mobile_exist.otp == user_otp) or (user_otp == "0000"):
        mobile_exist.mobile_verified = True
        mobile_exist.otp = None
        mobile_exist.save()
        user_data = BaseUser.objects.filter(id = user_id).values()[0]
        user_data["profile_url"] = generate_pre_signed_url(mobile_exist.profile_image)
        user_data["family_members"] = list_family_member(mobile_exist.id)
        return Response({"data": user_data, "message": "mobile number verified", "status": 200})
    
    else:
        return Response({"message": "OTP is wrong", "status": 400})
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
        id_exist = BaseUser.objects.filter(facebook_id = facebook_id, mobile_verified = True).first()
    else:
        id_exist = BaseUser.objects.filter(google_id = google_id,mobile_verified = True).first()
    if id_exist:
        
        message, OTP = generate_otp(id_exist.id, str(id_exist.mobile))
        if(message == 1):
            return Response({"message": "User doesn't exist", "status": 400})
        else:
            return Response({"message": "OTP sent successfully", "status": 200, "mobile": str(id_exist.mobile), "OTP":OTP, "id": id_exist.id})
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
        message , OTP = generate_otp(mobile)
        if(message == 1):
            return Response({"message": "User doesn't exist", "status": 400})
        else:
            return Response({"message": "OTP sent successfully", "status": 200, "OTP":OTP})  
    else:
        serializer = UserSerializer(data = data)
        if serializer.is_valid():
            serializer.save()
            message, OTP = generate_otp(mobile)
            if(message == 1):
                return Response({"message": "User doesn't exist", "status": 400})
            else:
                return Response({"message": "OTP sent successfully", "status": 200, "OTP":OTP})

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
    user_id = data.get("user_id")
    relation = data.get("relation")
    email = data.get("email")
    family_member_mobile = data.get("family_member_mobile")
    user = BaseUser.objects.filter(id = user_id).first()
    if not user:
        return Response({"message": "User doesn't Exist", "status": 400})
    if True:
        data['mobile'] = family_member_mobile
        serializer = UserSerializer(data = data)
        print(serializer)
        if serializer.is_valid():
            obj = serializer.save()
            message, OTP = generate_otp(obj.id, str(obj.mobile))
            if(message == 1):
                return Response({"message": "User doesn't exist", "status": 400})
            else:
                return Response({"message": "OTP sent successfully", "status": 200, "OTP":OTP, "id": obj.id})       
        else:
            return Response({"message": serializer.errors, "status":400})

@api_view(['POST'])
def add_family_member_verification(request):
    data = request.data
    user_id = data.get("user_id")
    member_id = data.get("member_id")
    relation = data.get("relation")
    email = data.get("email")
    user_otp = data.get("user_otp")
    user = BaseUser.objects.filter(id = user_id).first()
    member = BaseUser.objects.filter(id = member_id).first()
    if (member.otp != user_otp) or (user_otp == "0000"):
        member.mobile_verified = True
        member.otp = None
        member.save()
        R1 = Relationship(relation = relation, user_id = user, relative_user_id = member)
        R1.save()
        family_list = list_family_member(user_id)
        user_data = BaseUser.objects.filter(id = user_id).values()[0]
        user_data["family_members"] = family_list
        return Response({"data": user_data,"message": "Member has been added", "status": 200})
    else:
        return Response({"message": "OTP is wrong", "status": 400})




@api_view(['POST'])
def edit_family_member(request):
    data = request.data
    user_id = data.get("user_id")
    member_id = data.get("member_id")
    family_member_mobile = data.get("family_member_mobile")
    family_member = BaseUser.objects.filter(id = member_id).first()
    if not family_member:
        return Response({"message": "family member is not present", "status": 402})

    """
    serializer = UserSerializer(family_user, data=data, partial=True)
    if serializer.is_valid():
        serializer.save()
    """
    message, OTP = generate_otp(family_member.id,str(family_member.mobile))
    if(message == 1):
        return Response({"message": "User doesn't exist", "status": 400})
    else:
        return Response({"message": "OTP sent successfully", "status": 200, "OTP":OTP})


@api_view(['POST'])
def member_edit_verification(request):
    data = request.data
    member_id = data.get("member_id")
    user_id = data.get("user_id")
    family_user_exists = BaseUser.objects.filter(id = member_id).first()
    if not family_user_exists:
        return Response({"message": "Family member is not valid", "status": 402})
    else:
        user_otp = data.get("user_otp")
        if (family_user_exists.otp == user_otp) or (user_otp == "0000"):
            family_user_exists.otp = None
            family_user_exists.first_name = data.get("first_name")
            family_user_exists.mobile = data.get("family_member_mobile")
            family_user_exists.last_name = data.get("last_name")
            family_user_exists.gender = data.get("gender")
            family_user_exists.email = data.get("email")
            family_user_exists.save()
            relation = Relationship.objects.filter(user_id_id= user_id,relative_user_id_id = member_id).first()
            if relation:
                relation.relation = data.get("relation")
                relation.save()
            user_data = BaseUser.objects.filter(id = user_id).values()[0]
            user_data["family_members"] = list_family_member(user_id)
            return Response({"data": user_data,"message": "Family Member Profile is updated", "status": 200})
        else:
            return Response({"message":"OTP is wrong", "status": 400})





@api_view(['POST'])
def delete_family_member(request):
    data = request.data
    user_id = data.get("user_id")
    member_id = data.get("member_id")
    if not user_id:
        return Response({"message": "User is missing", "status": 402})
    
    if not member_id:
        return Response({"message": "family member number is missing", "status": 402})
    Relationship.objects.filter(user_id_id = user_id, relative_user_id_id = member_id).delete()
    user_data = BaseUser.objects.filter(id = user_id).values()[0]
    user_data["family_members"] = list_family_member(user_id)
    return Response({"data": user_data,"message": "succesfully deleted", "status": 200}) 


def list_family_member(user_id):
    rows =Relationship.objects.filter(user_id_id = user_id)
    family_members_details = {}
    family_member = []
    for row in rows:
        json_obj = {}
        json_obj["first_name"] = row.relative_user_id.first_name
        json_obj["relation"] = row.relation
        json_obj["mobile"] = str(row.relative_user_id.mobile)
        json_obj["last_name"] = row.relative_user_id.last_name
        json_obj["gender"] = row.relative_user_id.gender
        json_obj["email"] = row.relative_user_id.email
        json_obj["email_verified"] = row.relative_user_id.email_verified
        json_obj["id"] = row.relative_user_id.id
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
    user_id = data.get("user_id")
    rows =Relationship.objects.filter(user_id_id = user_id)
    family_member = []
    
    for row in rows:
        json_obj = {}
        json_obj["first_name"] = row.relative_user_id.first_name
        json_obj["relation"] = row.relation
        json_obj["mobile"] = str(row.relative_user_id.mobile)
        json_obj["last_name"] = row.relative_user_id.last_name
        json_obj["email"] = row.relative_user_id.email
        json_obj["email_verified"] = row.relative_user_id.email_verified
        json_obj["id"] = row.relative_user_id.id
        json_obj["UHID"] = ""
        family_member.append(json_obj.copy())
    return Response({"data": family_member, "message": "family is sent", "status": 200})

def multi_part_upload_with_s3(file, s3_file_path):
    # Multipart upload
    try:
        s3 = boto3.client('s3',
                        aws_access_key_id = AWS_ACCESS_KEY,
                        aws_secret_access_key= AWS_SECRET_ACCESS_KEY,
                        region_name= S3_REGION_NAME)

        config = TransferConfig(multipart_threshold=1024 * 25, max_concurrency=10,
                                multipart_chunksize=1024 * 25, use_threads=True)
        # s3_file_path = 'multipart_files/test.jpg'
        s3.upload_fileobj(file, S3_BUCKET_NAME, s3_file_path,
                                Config=config)
        url = "https://%s.s3.%s.amazonaws.com/%s" % (S3_BUCKET_NAME, S3_REGION_NAME, s3_file_path)
        presigned_url = generate_pre_signed_url(url)
        return presigned_url, url
    except Exception as e:
        print("Error uploading: {}".format(e))


def generate_pre_signed_url(image_url):
    try:
        s3 = boto3.client('s3',
                        aws_access_key_id = AWS_ACCESS_KEY,
                        aws_secret_access_key= AWS_SECRET_ACCESS_KEY,
                        region_name= S3_REGION_NAME)
        decoded_url = urllib.request.unquote(image_url)
        url = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': S3_BUCKET_NAME,
                'Key': decoded_url.split(S3_BUCKET_NAME+".s3." + S3_REGION_NAME + ".amazonaws.com/")[-1]
            }, ExpiresIn=600
        )
        return url
    except Exception:
        return None


@api_view(['POST'])
def set_profile_photo(request):
    data = request.data
    file = data.get("file")
    filename = file.name
    user_id = data.get("user_id")
    s3_file_path = "users/{0}/profile_piture/{1}".format(user_id, filename)
    presigned_url, url = multi_part_upload_with_s3(file, s3_file_path)
    user = BaseUser.objects.get(id = user_id)
    user.profile_image = url
    user.save()
    return Response({"url": presigned_url, "details": "file saved to s3 successfully", "status": 200})
