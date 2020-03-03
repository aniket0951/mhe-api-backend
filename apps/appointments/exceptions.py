from rest_framework.exceptions import APIException
from rest_framework import status


class PatientDoesNotExistsValidationException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'invalid_patient_id'
    default_detail = 'Patient does not Exist'

class DoctorDoesNotExistsValidationException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'invalid_doctor_id'
    default_detail = 'Doctor does not Exist'

class HospitalDoesNotExistsValidationException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'invalid_Hospital_id'
    default_detail = 'Hospital does not Exist'

class DepartmentDoesNotExistsValidationException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'invalid_department_id'
    default_detail = 'Deparment does not Exist'

class AppointmentDoesNotExistsValidationException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'invalid_appointment_identifier'
    default_detail = 'Appointment does not Exist'

