import math
import os

import pandas as pd
from django.core.management import BaseCommand, CommandError

from apps.patient_registration.models import Country
from apps.patient_registration.serializers import CountrySerializer


class Command(BaseCommand):
    help = "Create Country"

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str)

    def handle(self, *args, **options):

        if options['file'] == None:
            raise CommandError(
                "Option `--file=<master_data_country_resource_file _path>` must be specified.")

        try:
            if not os.path.isfile(os.path.abspath(options['file'])):
                print("--file does not exists.")
                exit()

            app_file = open(os.path.abspath(options['file']), 'rb')
            excel_object = pd.ExcelFile(app_file, engine='xlrd')

            if not 'Country Master' in excel_object.sheet_names:
                raise CommandError("`Country Master` sheet is missing!")

            saved_items, ignored_items = list(), list()
            required_country_keys = ['CTCOU_Code', 'CTCOU_Desc',
                                     'CTCOU_Active', 'CTCOU_DateActiveFrom',
                                     'CTCOU_DateActiveTo']

            country_master_data = excel_object.parse(
                'Country Master').to_dict('records')

            for row_number, each_country in enumerate(country_master_data, start=2):
                if not set(required_country_keys).issubset(set(each_country.keys())):
                    each_country['row_number'] = row_number
                    ignored_items.append(each_country)

                each_country['code'] = each_country.pop('CTCOU_Code')
                each_country['description'] = each_country.pop('CTCOU_Desc')
                each_country['is_active'] = each_country.pop(
                    'CTCOU_Active') == 'Y'
                each_country['from_date'] = each_country.pop(
                    'CTCOU_DateActiveFrom').date()

                if math.isnan(each_country['CTCOU_DateActiveTo']):
                    each_country['to_date'] = None
                else:
                    each_country['to_date'] = each_country.pop(
                        'CTCOU_DateActiveTo').date()

                serializer = CountrySerializer(data=each_country)

                if serializer.is_valid():
                    saved_items.append(each_country)
                    continue
                else:
                    each_country['row_number'] = row_number
                    each_country['reason'] = serializer.errors
                    ignored_items.append(each_country)

            serializer = CountrySerializer(
                data=saved_items, many=True)

            if serializer.is_valid():
                serializer.save()
            else:
                print('Error: ', serializer.errors)

            print("Ignored Countries:", ignored_items)
        except Exception as e:
            print(
                "Unexpected error occurred while import Country - {0}".format(e))
