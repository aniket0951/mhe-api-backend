import json
import os

from django.core.management import BaseCommand, CommandError
from rest_framework.test import APIClient
from tablib import Dataset

from apps.master_data.models import Hospital, Department
from apps.master_data.resources import BillingGroupResource

client = APIClient()


class Command(BaseCommand):
    help = "Create or Update Departments"

    def handle(self, *args, **options):
        try:
            all_hospitals = Hospital.objects.all()
            for each_hospital in all_hospitals:
                print("Started loading departments of {} hospital.".format(each_hospital.code))
                
                client.post('/api/master_data/departments',json.dumps({'location_code': each_hospital.code}), content_type='application/json')
                print("Completed loading departments of {} hospital.\n------------".format(each_hospital.code))

        except Exception as e: 
            print("Unexpected error occurred while loading Departments- {0}".format(e))
