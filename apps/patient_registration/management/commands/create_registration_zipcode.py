import math
import os

import pandas as pd
from django.core.management import BaseCommand, CommandError

from apps.patient_registration.models import Zipcode, City
from apps.patient_registration.serializers import ZipcodeSerializer


class Command(BaseCommand):
    help = "Create Zipcode"

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str)

    def handle(self, *args, **options):

        if options['file'] == None:
            raise CommandError(
                "Option `--file=<master_data_zipcode_resource_file _path>` must be specified.")

        try:
            if not os.path.isfile(os.path.abspath(options['file'])):
                print("--file does not exists.")
                exit()

            app_file = open(os.path.abspath(options['file']), 'rb')
            excel_object = pd.ExcelFile(app_file, engine='xlrd')

            if not 'Zip Master' in excel_object.sheet_names:
                raise CommandError("`Zip Master` sheet is missing!")

            saved_items, ignored_items = list(), list()
            required_zipcode_keys = ['CTZIP_Code', 'CTZIP_Desc', 'CTCIT_Code', 'CTCIT_Desc']

            zipcode_master_data = excel_object.parse(
                'Zip Master').to_dict('records')

            for row_number, each_zipcode in enumerate(zipcode_master_data, start=2):
                
                if not set(required_zipcode_keys).issubset(set(each_zipcode.keys())):
                    each_zipcode['row_number'] = row_number
                    ignored_items.append(each_zipcode)

                each_zipcode['code'] = each_zipcode.pop('CTZIP_Code')
                each_zipcode['description'] = each_zipcode.pop('CTZIP_Desc')
                if not City.objects.filter(description=each_zipcode['CTCIT_Desc']).exists():
                    each_zipcode['row_number'] = row_number
                    each_zipcode['reason'] = 'City not found!'
                    ignored_items.append(each_zipcode)
                else:
                    each_zipcode['city'] = City.objects.filter(description=each_zipcode['CTCIT_Desc']).first().id

                serializer = ZipcodeSerializer(data=each_zipcode)

                if serializer.is_valid():
                    saved_items.append(each_zipcode)
                    continue
                else:
                    each_zipcode['row_number'] = row_number
                    each_zipcode['reason'] = serializer.errors
                    ignored_items.append(each_zipcode)

            serializer = ZipcodeSerializer(
                data=saved_items, many=True)

            if serializer.is_valid():
                serializer.save()
            else:
                print('Error: ', serializer.errors)

            print("Ignored Countries:", ignored_items)
        except Exception as e:
            print(
                "Unexpected error occurred while import Zipcodes - {0}".format(e))
