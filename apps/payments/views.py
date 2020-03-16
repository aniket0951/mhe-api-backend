from django.shortcuts import render
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import parser_classes
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from apps.patients.exceptions import PatientDoesNotExistsValidationException
from rest_framework.decorators import api_view
from rest_framework.response import Response
from proxy.custom_views import ProxyView
from apps.patients.models import FamilyMember, Patient
import hashlib
import requests
import base64
import xml.etree.ElementTree as ET
import json
from random import randint

@api_view(['GET'])
def getData(request):
    param = {}
    token = {}
    token["auth"] = {}
    token["auth"]["user"] = "manipalhospitaladmin"
    token["auth"]["key"] = "ldyVqN8Jr1GPfmwBflC2uQcKX2uflbRP"
    token["username"] = "Patient"
    token["accounts"] = []
    account = {
        "patient_name": "Jane Doe",
        "account_number": "ACC1",
        "amount": "150.25",
        "email": "abc@xyz.com",
        "phone": "9876543210"
    }
    token["accounts"].append(account)
    token["processing_id"] = "process269"
    token["paymode"] = ""
    token["response_url"] = "https://mhedev.mantralabsglobal.com/api/payments/get_response"
    token["return_url"] = "https://www.google.com/"
    token["package_code"] = "ZURICH LIFE_IPHC"
    param["token"] = token
    param["mid"] = "ydLf7fPe"
    param["check_sum_hash"] = get_checksum(
        token["auth"]["user"], token["auth"]["key"], token["processing_id"],param["mid"] , "bDp0YXGlb0s4PEqdl2cEWhgGN0kFFEPD")
    param["mid"] = "ydLf7fPe"

    return Response(data=param)

@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([FormParser, MultiPartParser, JSONParser])
def getResponse(request):
    with open('data.json', 'a') as outfile:
        json.dump(request.data, outfile)
    return Response(data = request.data)




def get_hash_string(request, txnid):
    hash_string = auth.user+"|"+auth.key+"|"+processing_id +"|"+mid +"|" + secret_key
    return hash_string

def get_transaction_id():
    hash_object = hashlib.sha256(str(randint(0,9999)).encode("utf-8"))
    # take approprite length
    txnid = hash_object.hexdigest().lower()[0:32]
    return txnid

def get_checksum(user, key, processing_id, mid, secret_key):
    print(user, key, processing_id, mid, secret_key)
    hash_string = user + '|' + key + '|' + processing_id + '|' + mid + '|' + secret_key
    sha_signature = hashlib.sha256(hash_string.encode()).hexdigest()
    checksum = base64.b64encode(sha_signature.encode('ascii'))
    return checksum;




