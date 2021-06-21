import hashlib
import random
import time
import logging

from rest_framework.test import APIRequestFactory
from apps.health_packages.models import HealthPackage
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from apps.patients.models import Patient
from apps.master_data.models import FeedbackRecipients
from apps.patients.exceptions import UnablToSendEmailException

TO = "TO"
CC = "CC"
ALL = "ALL"

logger = logging.getLogger('django')

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

def get_user_name(patient_instance):
    user_name = ""
    if patient_instance.first_name:
        user_name += patient_instance.first_name
    if patient_instance.middle_name:
        user_name += " "+patient_instance.middle_name
    if patient_instance.last_name:
        user_name += " "+patient_instance.last_name
    return user_name

def get_hospital_code(patient_instance):
    return patient_instance.favorite_hospital.code if patient_instance and patient_instance.favorite_hospital and patient_instance.favorite_hospital.code else ""


def get_email_body(patient_instance,feedback_serializer):
    user_name = get_user_name(patient_instance) if patient_instance else ""
    user_email = patient_instance.email if patient_instance else ""
    user_mobile = patient_instance.mobile if patient_instance else ""
    user_uhid = patient_instance.uhid_number if patient_instance else ""
    user_favorite_hospital_name = patient_instance.favorite_hospital.description if patient_instance and patient_instance.favorite_hospital and patient_instance.favorite_hospital.description else ""
    user_favorite_hospital_code = get_hospital_code(patient_instance)
    user_rating = feedback_serializer.data.get("rating") or ""
    user_feedback = feedback_serializer.data.get("feedback") or ""
    user_platform = feedback_serializer.data.get("platform") or ""
    user_version = feedback_serializer.data.get("version") or ""
    return 'Hello,\nPlease find below the feedback received from a user. \n\nUser: {}\nMobile No.: {}\nEmail: {}\nUHID: {}\nPreferred Hospital: {} ({})\nRating: {}\nFeedback: {}\nPlatform: {}\nApp Version:{}\n\nThank you!'.format(
            user_name,
            user_mobile,
            user_email,
            user_uhid,
            user_favorite_hospital_name,
            user_favorite_hospital_code,
            user_rating,
            user_feedback,
            user_platform,
            user_version
        )

def get_feedback_recipients(patient_instance):
    hospital_code = get_hospital_code(patient_instance)
    feedback_recipients_data = { TO:[], CC:[] }
    feedback_recipients = FeedbackRecipients.objects.filter(hospital_code__in=[hospital_code,ALL])
    for feedback_recipient in feedback_recipients:
        if feedback_recipient.type and feedback_recipient.type in feedback_recipients_data:
            feedback_recipients_data[feedback_recipient.type].append(feedback_recipient.email)
    return feedback_recipients_data

def send_feedback_received_mail(feedback_serializer,patient_instance):
    try:
        if not settings.FEEDBACK_NOTIFICATION_EMAIL_SUBJECT:
            raise UnablToSendEmailException
        
        feedback_recipients_data = get_feedback_recipients(patient_instance)
        if not feedback_recipients_data.get(TO) and not feedback_recipients_data.get(CC):
            raise UnablToSendEmailException
        
        email = EmailMultiAlternatives(
                            subject=settings.FEEDBACK_NOTIFICATION_EMAIL_SUBJECT,
                            body=get_email_body(patient_instance,feedback_serializer),
                            from_email=settings.EMAIL_FROM_USER,
                            to=feedback_recipients_data.get(TO),
                            cc=feedback_recipients_data.get(CC)
                        )
        email_sent = email.send()

        if not email_sent:
            raise UnablToSendEmailException
    except Exception as e:
        logger.info("Exception while sending feedback email: %s"%str(e))

