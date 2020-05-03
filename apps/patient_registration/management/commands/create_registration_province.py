import math
import os

import pandas as pd
from django.core.management import BaseCommand, CommandError

from apps.patient_registration.models import Province, Region
from apps.patient_registration.serializers import ProvinceSerializer


class Command(BaseCommand):
    help = "Create Province"

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str)

    def handle(self, *args, **options):

        if options['file'] == None:
            raise CommandError(
                "Option `--file=<master_data_province_resource_file _path>` must be specified.")

        try:
            if not os.path.isfile(os.path.abspath(options['file'])):
                print("--file does not exists.")
                exit()

            app_file = open(os.path.abspath(options['file']), 'rb')
            excel_object = pd.ExcelFile(app_file, engine='xlrd')

            if not 'Provinince Master' in excel_object.sheet_names:
                raise CommandError("`Province Master` sheet is missing!")

            saved_items, ignored_items = list(), list()
            required_province_keys = ['PROV_Code', 'PROV_Desc', 'CTRG_Code', 'CTRG_Desc']

            province_master_data = excel_object.parse(
                'Provinince Master').to_dict('records')

            for row_number, each_province in enumerate(province_master_data, start=2):

                if not set(required_province_keys).issubset(set(each_province.keys())):
                    each_province['row_number'] = row_number
                    ignored_items.append(each_province)

                each_province['code'] = each_province.pop('PROV_Code')
                each_province['description'] = each_province.pop('PROV_Desc')
                if not Region.objects.filter(description=each_province['CTRG_Desc']).exists():
                    each_province['row_number'] = row_number
                    each_province['reason'] = 'Region not found!'
                    ignored_items.append(each_province)
                else:
                    each_province['region'] = Region.objects.filter(description=each_province['CTRG_Desc']).first().id

                serializer = ProvinceSerializer(data=each_province)

                if serializer.is_valid():
                    saved_items.append(each_province)
                    continue
                else:
                    each_province['row_number'] = row_number
                    each_province['reason'] = serializer.errors
                    ignored_items.append(each_province)

            serializer = ProvinceSerializer(
                data=saved_items, many=True)

            if serializer.is_valid():
                serializer.save()
            else:
                print('Error: ', serializer.errors)

            print("Ignored Provinces:", ignored_items)
        except Exception as e:
            print(
                "Unexpected error occurred while import Provinces - {0}".format(e))
