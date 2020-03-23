from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.patients.models import Patient
from manipal_api.settings import EMAIL_FROM_USER

from .exceptions import UnablToSendEmailException


def send_email_activation_otp(user_id, OTP):

    user = Patient.objects.get(id=user_id)
    # template_name = os.path.join(os.path.dirname(
    #     __file__), 'templates/reset_password.html')
    recipients = [user.email]

    # context = {
    #     'otp': OTP
    # }

    subject = 'Email Activation'

    text_content = 'Dear {}, Please enter this OTP {} to activate your email.'.format(
        user.first_name, OTP)

    # html_content = render_to_string(template_name, context)
    email = EmailMultiAlternatives(
        subject, text_content, EMAIL_FROM_USER, recipients)
    # email.attach_alternative(html_content, "text/html")
    email_sent = email.send()
    
    if not email_sent:
        raise UnablToSendEmailException
