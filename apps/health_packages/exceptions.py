from rest_framework import status
from rest_framework.exceptions import APIException


class FeatureNotAvailableException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'Online Booking Option for this location is not available'
    default_detail = 'Online Booking Option for this location is not available'