
import hashlib
import random
import time

from rest_framework.test import APIRequestFactory
from apps.health_packages.models import HealthPackage
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from apps.patients.models import Patient

from apps.patients.exceptions import UnablToSendEmailException

def cancel_and_refund_parameters(param, factory=APIRequestFactory()):
    return factory.post(
        '', param, format='json')

def rebook_parameters(instance, factory=APIRequestFactory()):
    param = {}
    param["app_id"] = instance.appointment_identifier
    health_packages = instance.health_package.all()
    code = ""
    for package in health_packages:
        if not code:
            code = package.code
        else:
            code = code + "||" + package.code
    param["package_code"] = code
    param["total_amount"] = str(instance.payment.amount)
    param["type"] = "H"
    param["receipt_no"] = instance.payment.receipt_number
    param["trans_id"] = instance.payment.transaction_id
    param["location_code"] = instance.hospital.code
    return factory.post(
        '', param, format='json')


def get_processing_id(*args):
    t = time.time()*1000
    r = random.random()*100000000000000000
    a = random.random()*100000000000000000
    processing_id = str(t)+' '+str(r)+' '+str(a)+' '+str(args)
    processing_id = hashlib.md5(processing_id.encode('utf-8')).hexdigest()
    return processing_id

def get_transaction_id(*args):
    t = time.time()*1000
    r = random.random()*100000000000000000
    a = random.random()*100000000000000000
    processing_id = str(t)+' '+str(r)+' '+str(a)+' '+str(args)
    processing_id = hashlib.md5(processing_id.encode('utf-8')).hexdigest()
    return processing_id

def get_user_name(feedback_serializer):
    user_name = ""
    if feedback_serializer.data.get("user_id"):
        patient_instance = Patient.objects.filter(id=feedback_serializer.data.get("user_id")).first()
        if patient_instance.first_name:
            user_name += patient_instance.first_name
        if patient_instance.middle_name:
            user_name += " "+patient_instance.middle_name
        if patient_instance.last_name:
            user_name += " "+patient_instance.last_name
    return user_name

def send_feedback_received_mail(feedback_serializer):

    user_name = get_user_name(feedback_serializer)
    user_rating = feedback_serializer.data.get("rating") or ""
    user_feedback = feedback_serializer.data.get("feedback") or ""
    user_platform = feedback_serializer.data.get("platform") or ""
    user_version = feedback_serializer.data.get("version") or ""

    recipients = settings.FEEDBACK_NOTIFICATION_EMAIL_RECIPIENTS
    subject = settings.FEEDBACK_NOTIFICATION_EMAIL_SUBJECT
    text_content = settings.FEEDBACK_NOTIFICATION_EMAIL_BODY.format(
        user_name,
        user_rating,
        user_feedback,
        user_platform,
        user_version
    )

    email = EmailMultiAlternatives(subject, text_content, settings.EMAIL_FROM_USER, recipients)
    email_sent = email.send()

    if not email_sent:
        raise UnablToSendEmailException