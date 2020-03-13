from rest_framework import status
from rest_framework.exceptions import APIException

class AppointmentDoesNotExistsValidationException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'invalid_appointment_identifier'
    default_detail = 'Appointment does not Exist'

class AppointmentAlreadyExistsException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'You have already booked an Appointment for this date'
    default_detail = 'You have already booked an Appointment for this date'
