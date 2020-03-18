from rest_framework.exceptions import APIException
from rest_framework import status


class ManipalAdminDoesNotExistsValidationException(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_code = 'invalid_manipal_admin'
    default_detail = 'Invalid email ID!'

