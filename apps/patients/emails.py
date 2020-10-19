from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.patients.models import FamilyMember, Patient

from .exceptions import UnablToSendEmailException


def send_email_activation_otp(user_id, otp_number):

    user = Patient.objects.get(id=user_id)
    recipients = [user.email]
    subject = 'Email Activation'
    text_content = 'Dear {}, Please enter this OTP {} to activate your email.'.format(
        user.first_name, otp_number)

    email = EmailMultiAlternatives(
        subject, text_content, settings.EMAIL_FROM_USER, recipients)
    email_sent = email.send()

    if not email_sent:
        raise UnablToSendEmailException


def send_family_member_email_activation_otp(user_id, otp_number):

    user = FamilyMember.objects.get(id=user_id)
    recipients = [user.email]
    subject = 'Email Activation'
    text_content = 'Dear {}, Please enter this OTP {} to activate your email.'.format(
        user.first_name, otp_number)

    email = EmailMultiAlternatives(
        subject, text_content, settings.EMAIL_FROM_USER, recipients)
    email_sent = email.send()

    if not email_sent:
        raise UnablToSendEmailException


def send_corporate_email_activation_otp(user_id ,email_id, otp_number):

    user = Patient.objects.get(id=user_id)
    recipients = [email_id]
    subject = 'Corporate Account OTP Verification'
    text_content = 'Dear {}, Please enter this OTP {} to verify your corporate account on Manipal Mobile apps'.format(
        user.first_name, otp_number)

    email = EmailMultiAlternatives(
        subject, text_content, settings.EMAIL_FROM_USER, recipients)
    email_sent = email.send()

    if not email_sent:
        raise UnablToSendEmailException
