import json
import logging
import os

from django.core.management import BaseCommand, CommandError
from apps.health_tests.models import HealthTest
from rest_framework.test import APIClient
from tablib import Dataset

from apps.master_data.models import Hospital, Department
from apps.master_data.resources import BillingGroupResource

client = APIClient()

logger = logging.getLogger('django')

class Command(BaseCommand):
    help = "Create or Update Health Packages"

    def handle(self, *args, **options):
        try:
            all_hospitals = Hospital.objects.all()
            logger.info("all_hospitals -- %s"%(str(all_hospitals)))
            all_health_test = HealthTest.objects.all()
            all_health_test.delete()
          #  all_health_test.save()
            for each_hospital in all_hospitals:
                logger.info("each_hospital -- %s"%(str(each_hospital)))
                print("Started loading Health Packages of {} hospital.".format(
                    each_hospital.code))
                
                client.post('/api/master_data/health_packages',
                                       json.dumps({'location_code': each_hospital.code}), content_type='application/json')
                print("Completed loading health packages of {} hospital.\n------------".format(each_hospital.code))
                logger.info("Completed loading health packages of %s hospital.\n------------"%(str(each_hospital.code)))
        except Exception as e:
            print("Unexpected error occurred while loading health packages- {0}".format(e))
            logger.info("Unexpected error occurred while loading health packages- %s"%(str(e)))