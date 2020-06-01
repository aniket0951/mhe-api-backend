import math
import os

import pandas as pd
from django.core.management import BaseCommand, CommandError

from apps.patient_registration.models import Language
from apps.patient_registration.serializers import LanguageSerializer


class Command(BaseCommand):
    help = "Create Language"

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str)

    def handle(self, *args, **options):

        if options['file'] == None:
            raise CommandError(
                "Option `--file=<master_data_language_resource_file _path>` must be specified.")

        try:
            if not os.path.isfile(os.path.abspath(options['file'])):
                print("--file does not exists.")
                exit()

            app_file = open(os.path.abspath(options['file']), 'rb')
            excel_object = pd.ExcelFile(app_file, engine='xlrd')

            if not 'Language Master' in excel_object.sheet_names:
                raise CommandError("`Language Master` sheet is missing!")

            saved_items, ignored_items = list(), list()
            required_language_keys = ['Desc', 'DescTranslated',
                                     'DateFrom', 'DateTo']

            language_master_data = excel_object.parse(
                'Language Master').to_dict('records')

            for row_number, each_language in enumerate(language_master_data, start=2):
                if not set(required_language_keys).issubset(set(each_language.keys())):
                    each_language['row_number'] = row_number
                    ignored_items.append(each_language)

                each_language['description'] = each_language.pop('Desc')
                each_language['translated_description'] = each_language.pop('DescTranslated')
                each_language['from_date'] = each_language.pop(
                    'DateFrom').date()

                if math.isnan(each_language['DateTo']):
                    each_language['to_date'] = None
                else:
                    each_language['to_date'] = each_language.pop(
                        'DateTo').date()

                serializer = LanguageSerializer(data=each_language)

                if serializer.is_valid():
                    saved_items.append(each_language)
                    continue
                else:
                    each_language['row_number'] = row_number
                    each_language['reason'] = serializer.errors
                    ignored_items.append(each_language)

            serializer = LanguageSerializer(
                data=saved_items, many=True)

            if serializer.is_valid():
                serializer.save()
            else:
                print('Error: ', serializer.errors)

            print("Ignored Languages:", ignored_items)
        except Exception as e:
            print(
                "Unexpected error occurred while import Language - {0}".format(e))
