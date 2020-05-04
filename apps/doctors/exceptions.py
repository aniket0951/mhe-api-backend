from rest_framework import status
from rest_framework.exceptions import APIException


class DoctorDoesNotExistsValidationException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'invalid_doctor_id'
    default_detail = 'Doctor does not Exist'
