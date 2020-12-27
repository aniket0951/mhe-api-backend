from rest_framework import status
from rest_framework.exceptions import APIException

class ProcessingIdDoesNotExistsValidationException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'invalid_processing_id'
    default_detail = 'Processing id does not Exist'


class MandatoryProcessingIdException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'invalid_processing_id'
    default_detail = 'Processing id is mandatory'

class MandatoryOrderIdException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'invalid_order_id'
    default_detail = 'Order id is mandatory'