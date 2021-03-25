from rest_framework import status
from rest_framework.exceptions import APIException


class InvalidRequest(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'invalid_request'
    default_detail = 'Invalid details to process this request!'

class UserNotRegisteredException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'invalid_selected_user'
    default_detail = 'Selected user is not registered!'