from rest_framework.exceptions import APIException
from rest_framework import status


class ManipalAdminDoesNotExistsValidationException(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_code = 'invalid_manipal_admin'
    default_detail = 'Invalid email ID!'

class ManipalAdminPasswordURLValidationException(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_code = 'invalid_manipal_admin_password_url'
    default_detail = 'This password link is not valid, looks like you are not registered with us.'

class ManipalAdminDisabledUserException(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_code = 'invalid_manipal_user_disabled'
    default_detail = 'The user is disabled'

class ManipalAdminPasswordURLExipirationValidationException(APIException):
    status_code = status.HTTP_410_GONE
    default_code = 'invalid_manipal_admin_password_url_expired'
    default_detail = 'This link is expired, please enter your email to send the link again.'