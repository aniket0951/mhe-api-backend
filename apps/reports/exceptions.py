from rest_framework import status
from rest_framework.exceptions import APIException


class ReportExistsException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'report_exists'
    default_detail = 'Report already exists!'
