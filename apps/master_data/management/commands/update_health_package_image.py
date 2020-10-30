import json

import requests
from django.conf import settings
from django.core.management import BaseCommand
from requests.auth import HTTPBasicAuth

from apps.health_packages.models import HealthPackage


class Command(BaseCommand):
    help = "Update Health Package Image Information"

    def handle(self, *args, **options):
        try:
            params = {"user": settings.HEALTH_PACKAGE_UPDATE_USER,
                      "pswd": settings.HEALTH_PACKAGE_UPDATE_PASSWORD}
            response_data = requests.request(
                'GET', settings.HEALTH_PACKAGE_UPDATE_API, params=params).text
            response_data = json.loads(response_data)
            print(response_data)
            for each_health_package in response_data:

                if not each_health_package['his_code']:
                    continue

                health_package_instance = HealthPackage.objects.filter(
                    code=each_health_package['his_code']).first()
                if health_package_instance:
                    health_package_instance.image = each_health_package['image-url']
                    health_package_instance.description = each_health_package['description']
                    health_package_instance.save()

        except Exception as e:
            print(
                "Unexpected error occurred while loading health package images- {0}".format(e))
