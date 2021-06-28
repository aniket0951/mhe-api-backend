import json
import os

from django.conf import settings
from django.core.management import BaseCommand, CommandError
from rest_framework.test import APIClient
from tablib import Dataset

from apps.master_data.models import Hospital, Department
from apps.master_data.resources import BillingGroupResource

client = APIClient()


class Command(BaseCommand):
    help = "Create or Update Doctors"

    def add_arguments(self, parser):
        parser.add_argument('--specific_date', nargs='+', type=str)

    def handle(self, *args, **options):
        try:
            if settings.ENVIRONMENT == "PROD":
                all_hospitals = Hospital.objects.all()
                specific_date = None
                if options and options.get('specific_date') and len(options.get('specific_date'))>0:
                    specific_date = str(options['specific_date'][0])
                for each_hospital in all_hospitals:
                    print("Started pushing statistics for {} hospital.".format(each_hospital.code))
                    client.post('/api/master_data/patient_app_statistics',
                                        json.dumps({
                                                'hospital_code': each_hospital.code,
                                                "specific_date": specific_date
                                            }), content_type='application/json')
                    print(
                        "Completed pushing statistics for {} hospital.\n------------".
                        format(each_hospital.code))

        except Exception as e:
            print(
                "Unexpected error occurred while loading doctors- {0}".format(e))