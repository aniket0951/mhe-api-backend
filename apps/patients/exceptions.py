from rest_framework.exceptions import APIException
from rest_framework import status


class PatientMobileExistsValidationException(APIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_code = 'mobile_number_exists'
    default_detail = 'Your mobile number is already registered with us!'


class PatientDoesNotExistsValidationException(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_code = 'invalid_patient'
    default_detail = 'Your are not registered with us!'


class PatientMobileDoesNotExistsValidationException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'invalid_patient_mobile'
    default_detail = 'Your are not registered with us!'


class InvalidCredentialsException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'invalid_credentials'
    default_detail = 'Your have entered invalid credentials!'


class InvalidEmailOTPException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'invalid_email_otp'
    default_detail = 'Your have entered invalid OTP!'


class UnablToSendEmailException(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_code = 'unable_to_send_email'
    default_detail = 'We are unable to send email at this moment!'


class OTPExpiredException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'otp_expired'
    default_detail = 'OTP is expired!'


class PatientOTPExceededLimitException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'otp_limit_exceeded'
    default_detail = 'You have exceeded your OTP limit, please login after some time.'


class InvalidUHID(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'invalid_uhid'
    default_detail = 'You have entered an invalid UHID.'
