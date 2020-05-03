import math
import os

import pandas as pd
from django.core.management import BaseCommand, CommandError

from apps.patient_registration.models import Region, Country
from apps.patient_registration.serializers import RegionSerializer


class Command(BaseCommand):
    help = "Create Region"

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str)

    def handle(self, *args, **options):

        if options['file'] == None:
            raise CommandError(
                "Option `--file=<master_data_region_resource_file _path>` must be specified.")

        try:
            if not os.path.isfile(os.path.abspath(options['file'])):
                print("--file does not exists.")
                exit()

            app_file = open(os.path.abspath(options['file']), 'rb')
            excel_object = pd.ExcelFile(app_file, engine='xlrd')

            if not 'Region Master' in excel_object.sheet_names:
                raise CommandError("`Region Master` sheet is missing!")

            saved_items, ignored_items = list(), list()
            required_region_keys = ['CTRG_Code', 'CTRG_Desc', 'CTCOU_Desc']

            region_master_data = excel_object.parse(
                'Region Master').to_dict('records')

            for row_number, each_region in enumerate(region_master_data, start=2):
                if not set(required_region_keys).issubset(set(each_region.keys())):
                    each_region['row_number'] = row_number
                    ignored_items.append(each_region)

                each_region['code'] = each_region.pop('CTRG_Code')
                each_region['description'] = each_region.pop('CTRG_Desc')

                if not Country.objects.filter(description=each_region['CTCOU_Desc']).exists():
                    each_region['row_number'] = row_number
                    each_region['reason'] = 'Country not found!'
                    ignored_items.append(each_region)
                else:
                    each_region['country'] = Country.objects.filter(
                        description=each_region['CTCOU_Desc']).first().id

                serializer = RegionSerializer(data=each_region)

                if serializer.is_valid():
                    saved_items.append(each_region)
                    continue
                else:
                    each_region['row_number'] = row_number
                    each_region['reason'] = serializer.errors
                    ignored_items.append(each_region)

            serializer = RegionSerializer(
                data=saved_items, many=True)

            if serializer.is_valid():
                serializer.save()
            else:
                print('Error: ', serializer.errors)

            print("Ignored Regions:", ignored_items)
        except Exception as e:
            print(
                "Unexpected error occurred while import Regions - {0}".format(e))
