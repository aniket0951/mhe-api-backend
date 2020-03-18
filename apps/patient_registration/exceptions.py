from rest_framework import status
from rest_framework.exceptions import APIException

class FieldMissingValidationException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'Mandatory Field Missing'
    default_detail = 'Mandatory Field Missing'