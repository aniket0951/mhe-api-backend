import base64
import hashlib
import random
import time

from django.conf import settings

from apps.payments.models import PaymentHospitalKey
from rest_framework.serializers import ValidationError


def get_payment_param(data=None):
    param = {}
    token = {}
    processing_id = get_processing_id()
    token["auth"] = {}
    token["auth"]["user"] = settings.SALUCRO_AUTH_USER
    token["auth"]["key"] = settings.SALUCRO_AUTH_KEY
    token["username"] = settings.SALUCRO_USERNAME
    location_code = data["location_code"]
    if not data["account"]:
        raise ValidationError("Account is empty")
    if not data["account"]["email"]:
        data["account"]["email"] = "manipalhospitals.app@gmail.com"
    token["accounts"].append(data["account"])
    token["processing_id"] = processing_id
    token["paymode"] = ""
    token["response_url"] = settings.SALUCRO_RESPONSE_URL
    token["return_url"] = settings.SALUCRO_RETURN_URL
    token["transaction_type"] = ""
    hospital_key_info = PaymentHospitalKey.objects.filter(
        hospital_id__code=location_code).first()
    if not hospital:
        raise ValidationError("Hospital does not exist")
    mid = hospital_key_info.mid
    secret_key = hospital_key_info.secret_key
    param["token"] = token
    param["mid"] = mid
    param["check_sum_hash"] = get_checksum(
        settings.SALUCRO_AUTH_USER, settings.SALUCRO_AUTH_KEY, processing_id, mid, secret_key)
    return param


def get_processing_id(*args):
    t = time.time()*1000
    r = random.random()*100000000000000000
    a = random.random()*100000000000000000
    processing_id = str(t)+' '+str(r)+' '+str(a)+' '+str(args)
    processing_id = hashlib.md5(processing_id.encode('utf-8')).hexdigest()
    return processing_id


def get_checksum(user, key, processing_id, mid, secret_key):
    hash_string = user + '|' + key + '|' + \
        processing_id + '|' + mid + '|' + secret_key
    sha_signature = hashlib.sha256(hash_string.encode()).hexdigest()
    checksum = base64.b64encode(sha_signature.encode('ascii'))
    return checksum
