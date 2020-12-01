import json

import requests
from django.utils.timezone import datetime
from rest_framework.test import APIClient
from django.conf import settings
from django.core.management import BaseCommand
from requests.auth import HTTPBasicAuth

client = APIClient()

from apps.health_packages.models import HealthPackagePricing


class Command(BaseCommand):
    help = "Update Health Package Image Information"

    def handle(self, *args, **options):
        try:
            all_health_packages = HealthPackagePricing.objects.all()
            for each_health_package in all_health_packages:
                
                location_code = each_health_package.hospital.code
                package = each_health_package.health_package.code
                response = client.post('/api/health_packages/health_package_price',
                                   json.dumps({'location_code': location_code, 'package_code': package}), content_type='application/json')
                
                if response.status_code == 200 and response.data["success"] == True:
                    try:
                        health_package_data = response.data["data"]
                        start_date = health_package_data.get("PackageStartDate", None)
                        end_date = health_package_data.get("PackageEndDate", None)
                        discount_start_date = health_package_data.get("DiscountStartDate", None)
                        discount_end_date = health_package_data.get("DiscountEndDate", None)
                        discount_percentage = health_package_data.get("Discount", None)

                        if not discount_percentage:
                            discount_percentage = 0

                        if start_date:
                            start_date = datetime.strptime(
                                start_date, '%d/%m/%Y').date()

                        if not start_date:
                            start_date = None
                        
                        if end_date:
                            end_date = datetime.strptime(
                                end_date, '%d/%m/%Y').date()

                        if not end_date:
                            end_date = None

                        if discount_start_date:
                            discount_start_date = datetime.strptime(
                                discount_start_date, '%d/%m/%Y').date()

                        if not discount_start_date:
                            discount_start_date = None

                        if discount_end_date:
                            discount_end_date = datetime.strptime(
                                discount_end_date, '%d/%m/%Y').date()

                        if not discount_end_date:
                            discount_end_date = None

                        each_health_package.price = health_package_data["Price"]
                        each_health_package.start_date = start_date
                        each_health_package.end_date = end_date
                        each_health_package.discount_start_date = discount_start_date
                        each_health_package.discount_end_date = discount_end_date
                        each_health_package.discount_percentage = discount_percentage
                        each_health_package.save()
        
                    except Exception as e:
                        print(e)

        except Exception as e:
            print(
                "Unexpected error occurred while loading health package prices- {0}".format(e))
