import base64
import hashlib
import random
import time

from django.conf import settings

from apps.payments.models import PaymentHospitalKey
from rest_framework.serializers import ValidationError
from apps.appointments.models import Appointment


def get_refund_param(data=None):
    param = {}
    appointment_identifier = data["appointment_identifier"]
    appointment_instance = Appointment.objects.filter(appointment_identifier = appointment_identifier).first()
    if not appointment_instance:
        raise ValidationError("Appointment does not Exist")
    location_code = appointment_instance.hospital.code
    hospital_key_info = PaymentHospitalKey.objects.filter(
        hospital_id__code=location_code).first()
    if not hospital_key_info:
        raise ValidationError("Hospital does not exist")
    mid = hospital_key_info.mid
    secret_key = hospital_key_info.secret_key
    param["processing_id"] = get_processing_id()
    param["mid"] = mid
    param["auth_user"] = settings.SALUCRO_AUTH_USER
    param["auth_key"] = settings.SALUCRO_AUTH_KEY
    param["username"] = settings.SALUCRO_USERNAME
    param["paymode"] = "payment-refund"
    patient = appointment_instance.patient
    if appointment_instance.family_member:
        patient = appointment_instance.family_member
    if not appointment_instance.payment_appointment.exists():
        return 
    param["patient_name"] = patient.first_name
    param["account_number"] = patient.uhid_number
    param["amount"] = appointment_instance.refundable_amount
    param["email"] = patient.email
    param["transaction_id"] = appointment_instance.payment_appointment.get().processing_id
    param["check_sum_hash"] = get_checksum(param, secret_key)
    return param


def get_processing_id(*args):
    t = time.time()*1000
    r = random.random()*100000000000000000
    a = random.random()*100000000000000000
    processing_id = str(t)+' '+str(r)+' '+str(a)+' '+str(args)
    processing_id = hashlib.md5(processing_id.encode('utf-8')).hexdigest()
    return processing_id


def get_checksum(param, secret_key):
    hash_string = param["processing_id"] + '|' + param["mid"] + '|' + \
        param["auth_user"] + '|' + param["auth_key"] + '|' + param["username"] + '|' + \
            param["paymode"] + '|' + param["patient_name"] + '|' + param["account_number"] +   '|' + \
                str(param["amount"]) + '|' + param["transaction_id"] + '|' + "LEVg8IWHfgRSjyFahy58KVKpdRVw7qJt"

    sha_signature = hashlib.sha256(hash_string.encode()).hexdigest()
    checksum = base64.b64encode(sha_signature.encode('ascii'))
    return checksum
