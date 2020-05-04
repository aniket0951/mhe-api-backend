from rest_framework import status
from rest_framework.exceptions import APIException


class HospitalDoesNotExistsValidationException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'invalid_Hospital_id'
    default_detail = 'Hospital does not Exist'


class DepartmentDoesNotExistsValidationException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'invalid_department_id'
    default_detail = 'Deparment does not Exist'


class InvalidHospitalCodeValidationException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'Invalid location code'
    default_detail = 'Invalid location code'


class HospitalCodeMissingValidationException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'Missing hospital location code'
    default_detail = 'Missing hospital location code'


class DoctorHospitalCodeMissingValidationException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'Missing doctors location code.'
    default_detail = 'Missing doctors location code.'


class ItemOrDepartmentDoesNotExistsValidationException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'Invalid location or item code.'
    default_detail = 'Invalid location or item code.'
