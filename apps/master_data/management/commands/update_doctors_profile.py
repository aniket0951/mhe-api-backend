import json

import requests
from django.core.management import BaseCommand
from apps.doctors.models import Doctor


class Command(BaseCommand):
    help = "Update Doctors Profile Information"

    def handle(self, *args, **options):
        try:
            response_data = requests.request(
                'GET', 'https://www.manipalhospitals.com/PatientAPI').text
            response_data = json.loads(response_data)
            for each_doctor_record in response_data:
                if not each_doctor_record['DoctorCode']:
                    continue

                doctor_details = dict()
                for index, key in enumerate(sorted(each_doctor_record.keys())):
                    if key in ['qualification', 'designation', 'field_expertise',
                               'languages_spoken',
                               'awards_achievements', 'fellowship_membership', 'photo']:
                        doctor_details[key] = each_doctor_record[key]

                Doctor.objects.filter(
                    code=each_doctor_record['DoctorCode']).update(**doctor_details)

        except Exception as e:
            print(
                "Unexpected error occurred while loading doctors- {0}".format(e))
