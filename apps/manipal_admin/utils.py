from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.manipal_admin.models import ManipalAdmin
from manipal_api.settings import EMAIL_FROM_USER


def send_reset_password_email(request, user_id):

    user = ManipalAdmin.objects.get(id=user_id)
    # template_name = os.path.join(os.path.dirname(
    #     __file__), 'templates/reset_password.html')
    recipients = [user.email]
    kwargs = {
        "uidb64": urlsafe_base64_encode(force_bytes(user.id)),
        "token": default_token_generator.make_token(user)
    }
    password_reset_url = reverse(
        'manipal_admin:password_reset', kwargs=kwargs)

    modified_activation_url = "/api" + \
        "".join(password_reset_url.split('api')[1:])

    activate_url = "{0}://{1}{2}".format(request.scheme,
                                         request.get_host(), modified_activation_url)
    # context = {
    #     'user': user.name,
    #     'activate_url': activate_url,
    # }

    subject = 'FORGOT PASSWORD'

    text_content = 'Dear {}, Please click this link {} to reset your password.'.format(
        user.name, activate_url)

    # html_content = render_to_string(template_name, context)
    email = EmailMultiAlternatives(
        subject, text_content, EMAIL_FROM_USER, recipients)
    # email.attach_alternative(html_content, "text/html")
    email.send()
