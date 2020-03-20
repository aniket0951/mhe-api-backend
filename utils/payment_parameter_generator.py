from manipal_api.settings import (SALUCRO_AUTH_KEY, SALUCRO_AUTH_USER,
                                  SALUCRO_MID, SALUCRO_RESPONSE_URL,
                                  SALUCRO_RETURN_URL, SALUCRO_USERNAME, SALUCRO_SECRET_KEY)

import base64
import hashlib
from random import randint

def get_payment_param(data =None):
    param = {}
    token = {}
    processing_id = get_processing_id()
    token["auth"] = {}
    token["auth"]["user"] = SALUCRO_AUTH_USER
    token["auth"]["key"] = SALUCRO_AUTH_KEY
    token["username"] = SALUCRO_USERNAME
    token["accounts"] = []
    token["accounts"].append(data["account"])
    token["processing_id"] = processing_id
    token["paymode"] = ""
    token["response_url"]=SALUCRO_RESPONSE_URL
    token["return_url"] = SALUCRO_RETURN_URL
    token["transaction_type"] = ""
    param["token"] = token
    param["mid"] = SALUCRO_MID
    param["check_sum_hash"] = get_checksum(SALUCRO_AUTH_USER, SALUCRO_AUTH_KEY,processing_id ,SALUCRO_MID, SALUCRO_SECRET_KEY)
    return param

def get_processing_id():
    hash_object = hashlib.sha256(str(randint(0, 9999)).encode("utf-8"))
    processing_id = hash_object.hexdigest().lower()[0:32]
    return processing_id

def get_checksum(user, key, processing_id, mid, secret_key):
    hash_string = user + '|' + key + '|' + \
        processing_id + '|' + mid + '|' + secret_key
    sha_signature = hashlib.sha256(hash_string.encode()).hexdigest()
    checksum = base64.b64encode(sha_signature.encode('ascii'))
    return checksum
