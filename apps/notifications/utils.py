from rest_framework.test import APIRequestFactory
from apps.health_packages.models import HealthPackage

def cancel_parameters(param, factory=APIRequestFactory()):
    return factory.post(
        '', param, format='json')

