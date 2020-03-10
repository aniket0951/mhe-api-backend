import json
import os

from django.core.management import BaseCommand, CommandError
from rest_framework.test import APIClient
from tablib import Dataset

from apps.master_data.models import Hospital, Department
from apps.master_data.resources import BillingGroupResource

client = APIClient()


class Command(BaseCommand):
    help = "Create or Update lab and radiology items"

    def handle(self, *args, **options):
        try:
            all_hospitals = Hospital.objects.all()
            for each_hospital in all_hospitals:
                print("Started loading lab and radiology items of {} hospital.".format(
                    each_hospital.code))
                if each_hospital.code == 'MMH':
                    continue
                
                client.post('/api/master_data/lab_and_radiology_items',
                                       json.dumps({'location_code': each_hospital.code}), content_type='application/json')
                print(
                    "Completed loading lab and radiology items of {} hospital.\n------------".
                    format(each_hospital.code))

        except Exception as e:
            print(
                "Unexpected error occurred while loading lab and radiology items- {0}".format(e))
