from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password

from apps.patients.models import Patient

class CustomPatientAuthBackend(BaseBackend):

    # Create an authentication method
    # This is called by the standard Django login procedure
    def authenticate(self, request, username=None, password=None):
        try:
            # Try to find a user matching your username
            patient = Patient.objects.get(
                mobile=username)
            match_password = check_password(password, patient.password)
            if match_password:
                return patient
        except Exception:
            pass
        return None

    # Required for your backend to work properly - unchanged in most scenarios
    def get_user(self, user_id):
        try:
            return get_user_model().objects.get(pk=user_id)
        except Exception:
            return None
