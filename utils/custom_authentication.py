from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password

from apps.patients.models import Patient

# from apps.patients.exceptions import PatientMobileDoesNotExistsValidationException


class CustomPatientAuthBackend(BaseBackend):

    # Create an authentication method
    # This is called by the standard Django login procedure
    def authenticate(self, request, username=None, password=None):
        try:
            # Try to find a user matching your username
            patient = Patient.objects.get(
                mobile=username, is_primary_account=True)
            match_password = check_password(password, patient.password)
            if match_password:
                # user_instance = get_user_model().objects.get(id=patient.id)
                return patient
        # except Patient.DoesNotExist:
        #         raise PatientMobileDoesNotExistsValidationException
        except Exception as e:
            print(e)
        return None

    # Required for your backend to work properly - unchanged in most scenarios
    def get_user(self, user_id):
        try:
            return get_user_model().objects.get(pk=user_id)
        except Exception:
            return None
