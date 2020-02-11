from django.shortcuts import render
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.contrib import messages
import logging, traceback
import students.constants as constants
import students.config as config
import hashlib
import requests
import base64
from random import randint
from django.views.decorators.csrf import csrf_exempt


def get_data(request)


def payment(request):   
    data = {}
    txnid = get_transaction_id()
    hash_ = generate_hash(request, txnid)
    hash_string = get_hash_string(request, txnid)
    checksum = get_checksum()


    # use constants file to store constant values.
    # use test URL for testing
    data["action"] = constants.PAYMENT_URL_LIVE 
    data["amount"] = float(constants.PAID_FEE_AMOUNT)
    data["productinfo"]  = constants.PAID_FEE_PRODUCT_INFO
    data["key"] = config.KEY
    data["txnid"] = txnid
    data["hash"] = hash_
    data["hash_string"] = hash_string
    data["firstname"] = request.session["student_user"]["name"]
    data["email"] = request.session["student_user"]["email"]
    data["phone"] = request.session["student_user"]["mobile"]
    data["service_provider"] = constants.SERVICE_PROVIDER
    data["furl"] = request.build_absolute_uri(reverse("students:payment_failure"))
    data["surl"] = request.build_absolute_uri(reverse("students:payment_success"))
    return render(data)

def generate_hash(request, txnid):
    try:
        # get keys and SALT from dashboard once account is created.
        # hashSequence = "key|txnid|amount|productinfo|firstname|email|udf1|udf2|udf3|udf4|udf5|udf6|udf7|udf8|udf9|udf10"
        hash_string = get_hash_string(request,txnid)
        generated_hash = hashlib.sha512(hash_string.encode('utf-8')).hexdigest().lower()
        return generated_hash
    except Exception as e:
        # log the error here.
        logging.getLogger("error_logger").error(traceback.format_exc())
        return None

def get_hash_string(request, txnid):
    hash_string = auth.user+"|"+auth.key+"|"+processing_id +"|"+mid +"|" + secret_key
    return hash_string

def get_transaction_id():
    hash_object = hashlib.sha256(str(randint(0,9999)).encode("utf-8"))
    # take approprite length
    txnid = hash_object.hexdigest().lower()[0:32]
    return txnid

def get_checksum(user, key, processing_id, mid, secret_key):
    hash_string = user + "|" + key + "|" + processing_id + "|"+ mid + "|" + secret_key
    checksum = base64.b64encode(hashlib.sha256(hash_string.encode("utf-8")).digest())
    return checksum




