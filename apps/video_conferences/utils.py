from apps.health_packages.models import HealthPackage
from rest_framework.test import APIRequestFactory


def create_room_parameters(param, factory=APIRequestFactory()):
    return factory.post(
        '', param, format='json')
