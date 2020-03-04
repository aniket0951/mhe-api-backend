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