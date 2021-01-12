import base64
import datetime
import hashlib
import random
import time
from datetime import datetime

from django.conf import settings

from apps.appointments.models import Appointment
from apps.payments.models import PaymentHospitalKey
from rest_framework.serializers import ValidationError


def get_refund_param_for_razorpay(data=None):
    param = {}
    
    appointment_instance = get_appointment_instance(data.get("appointment_identifier"))
    hospital_key_info = get_hospital_key_info(appointment_instance.hospital.code)
    mid = hospital_key_info.mid
    secret_key = hospital_key_info.secret_key

    param["processing_id"] = get_processing_id()
    param["mid"] = mid

    # param["auth_user"] = settings.SALUCRO_AUTH_USER
    param["auth_key"] = secret_key
    # param["paymode"] = "payment-refund"

    param = set_patient(appointment_instance,param)
    param = set_refund_amount(appointment_instance,param)

    instance = appointment_instance.payment_appointment.filter(status="success").first()
    if instance:
        param["transaction_id"] = instance.processing_id
    
    return param

def set_refund_amount(appointment_instance,param):
    if appointment_instance.appointment_date >= datetime.now().date():
        param["amount"] = appointment_instance.consultation_amount
        if appointment_instance.appointment_date == datetime.now().date():
            date_time_slot = datetime.combine(
                datetime.now(), appointment_instance.appointment_slot)
            date_time_now = datetime.combine(
                datetime.now(), datetime.now().time())
            time_delta = (
                date_time_slot - date_time_now).total_seconds()/3600
            if time_delta >= 2 and time_delta <= 4:
                param["amount"] = appointment_instance.consultation_amount - 100
            if time_delta < 2:
                param["amount"] = 0.0
    return param

def set_patient(appointment_instance,param):
    patient = get_patient_object(appointment_instance)
    param["username"] = patient.first_name.replace(" ", "")
    param["patient_name"] = patient.first_name.replace(" ", "")
    param["account_number"] = patient.uhid_number
    param["email"] = patient.email
    return param

def get_patient_object(appointment_instance):
    patient = appointment_instance.patient
    if appointment_instance.family_member:
        patient = appointment_instance.family_member
    if not appointment_instance.payment_appointment.exists() or appointment_instance.appointment_date < datetime.now().date():
        return ValidationError("Appointment is not valid!")
    return patient

def get_hospital_key_info(location_code):
    if not location_code:
        raise ValidationError("Please provide location code!")
    hospital_key_info = PaymentHospitalKey.objects.filter(
        hospital_id__code=location_code).first()
    if not hospital_key_info:
        raise ValidationError("Hospital does not exist")
    if not hospital_key_info.secret_key:
        raise ValidationError("Payment settings for the hospital are not configured")
    return hospital_key_info

def get_appointment_instance(appointment_identifier):
    if not appointment_identifier:
        raise ValidationError("Please provide Appointment Identifier!")
    appointment_instance = Appointment.objects.filter(
        appointment_identifier=appointment_identifier).first()
    if not appointment_instance:
        raise ValidationError("Appointment does not Exist")
    return appointment_instance

def get_processing_id(*args):
    t = time.time()*1000
    r = random.random()*100000000000000000
    a = random.random()*100000000000000000
    processing_id = str(t)+' '+str(r)+' '+str(a)+' '+str(args)
    processing_id = hashlib.md5(processing_id.encode('utf-8')).hexdigest()
    return processing_id
