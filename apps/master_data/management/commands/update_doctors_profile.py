import json
import logging

import requests
from django.conf import settings
from django.core.management import BaseCommand
from requests.auth import HTTPBasicAuth
from utils.custom_validation import ValidationUtil
from apps.doctors.models import Doctor

logger = logging.getLogger('django')


class Command(BaseCommand):
    help = "Update Doctors Profile Information"

    def handle(self, *args, **options):
        try:
            auth = HTTPBasicAuth(
                settings.DOCTOR_PROFILE_USERNAME, settings.DOCTOR_PROFILE_PASSWORD)

            response_data = requests.request(
                'GET', settings.PATIENT_PROFILE_SYNC_API, auth=auth).text
            response_data = json.loads(response_data)
            logger.info(response_data)
            for each_doctor_record in response_data:

                if not each_doctor_record['DoctorCode']:
                    continue

                doctor_details = dict()
                for key in sorted(each_doctor_record.keys()):

                    if key == "doc.qualification":
                        doctor_details["qualification"] = each_doctor_record[key]

                    if key == "doc_codes.designation":
                        doctor_details["designation"] = each_doctor_record[key]

                    if key == "doc.field_expertise":
                        doctor_details["field_expertise"] = each_doctor_record[key]

                    if key == "doc.languages_spoken":
                        doctor_details["languages_spoken"] = each_doctor_record[key]

                    if key == "doc.awards_achievements":
                        doctor_details["awards_achievements"] = each_doctor_record[key]

                    if key == "doc.talks_publications":
                        doctor_details["talks_publications"] = ValidationUtil.cleanhtml(each_doctor_record[key]) if each_doctor_record[key] else None
                    
                    if key == "'doc.fellowship_membership":
                        doctor_details["'fellowship_membership"] = each_doctor_record[key]

                    if key == "photo":
                        doctor_details[key] = each_doctor_record[key]

                    if key == "doc_name":
                        doctor_details["name"] = each_doctor_record[key]

                Doctor.objects.filter(
                    code=each_doctor_record['DoctorCode']).update(**doctor_details)

        except Exception as e:
            print("Unexpected error occurred while loading doctors- {0}".format(e))
