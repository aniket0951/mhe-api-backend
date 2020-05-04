import math
import os

import pandas as pd
from django.core.management import BaseCommand, CommandError

from apps.patient_registration.models import City, Province
from apps.patient_registration.serializers import CitySerializer


class Command(BaseCommand):
    help = "Create City"

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str)

    def handle(self, *args, **options):

        if options['file'] == None:
            raise CommandError(
                "Option `--file=<master_data_city_resource_file _path>` must be specified.")

        try:
            if not os.path.isfile(os.path.abspath(options['file'])):
                print("--file does not exists.")
                exit()

            app_file = open(os.path.abspath(options['file']), 'rb')
            excel_object = pd.ExcelFile(app_file, engine='xlrd')

            if not 'City Master' in excel_object.sheet_names:
                raise CommandError("`City Master` sheet is missing!")

            saved_items, ignored_items = list(), list()
            required_city_keys = ['CTCIT_Code', 'CTCIT_Desc', 'PROV_Code', 'PROV_Desc']

            city_master_data = excel_object.parse(
                'City Master').to_dict('records')

            for row_number, each_city in enumerate(city_master_data, start=2):
                
                if not set(required_city_keys).issubset(set(each_city.keys())):
                    each_city['row_number'] = row_number
                    ignored_items.append(each_city)

                each_city['code'] = each_city.pop('CTCIT_Code')
                each_city['description'] = each_city.pop('CTCIT_Desc')
                if not Province.objects.filter(description=each_city['PROV_Desc']).exists():
                    each_city['row_number'] = row_number
                    each_city['reason'] = 'Province not found!'
                    ignored_items.append(each_city)
                else:
                    each_city['province'] = Province.objects.filter(description=each_city['PROV_Desc']).first().id

                serializer = CitySerializer(data=each_city)

                if serializer.is_valid():
                    saved_items.append(each_city)
                    continue
                else:
                    each_city['row_number'] = row_number
                    each_city['reason'] = serializer.errors
                    ignored_items.append(each_city)

            serializer = CitySerializer(
                data=saved_items, many=True)

            if serializer.is_valid():
                serializer.save()
            else:
                print('Error: ', serializer.errors)

            print("Ignored Cities:", ignored_items)
        except Exception as e:
            print(
                "Unexpected error occurred while import Cities - {0}".format(e))
