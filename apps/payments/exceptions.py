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

class NoResponseFromRazorPayException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'invalid_razorpay_response'
    default_detail = 'No response from Razorpay'

class UHIDRegistrationFailedException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'invalid_UHID_registration_response'
    default_detail = 'UHID registration failed'

class InvalidGeneratedUHIDException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'invalid_generated_UHID'
    default_detail = 'Generated UHID is invalid'

class AppointmentCreationFailedException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'invalid_appointment_creation_response'
    default_detail = 'Appointment creation failed'

class TransactionFailedException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'invalid_transaction_response'
    default_detail = 'Transaction failed'

class UnsuccessfulPaymentException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'invalid_payment_status'
    default_detail = 'The payment was unsuccessful'
