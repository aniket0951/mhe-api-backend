import json
import os

from django.core.files import File
from django.core.management import BaseCommand, CommandError
from tablib import Dataset

from apps.master_data.resources import SpecialisationResource


class Command(BaseCommand):
    help = "Create Specialisations"

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str)

    def handle(self, *args, **options):

        if options['file'] == None:
            raise CommandError(
                "Option `--file=<master_data_specialisation_file _path>` must be specified.")

        try:
            if not os.path.isfile(os.path.abspath(options['file'])):
                print("--file does not exists.")
                exit()
            if not options['file'].endswith('.csv'):
                print("--file should be a csv file.")
                exit()

            app_file = open(os.path.abspath(options['file']), 'rb')
            new_specialisations = File(app_file)

            specialisation_resource = SpecialisationResource()
            dataset = Dataset()
            imported_data = dataset.load(
                new_specialisations.read().decode('utf-8'), format='csv')
            result = specialisation_resource.import_data(
                dataset, dry_run=True)  # Test the data import

            if not result.has_errors():
                specialisation_resource.import_data(
                    dataset, dry_run=False)  # Actually import now
                print("Specialisation imported successfullly!")
            else:
                print("Unable to import Specialisation data!")

        except Exception as e:
            print(
                "Unexpected error occurred while import Specialisation - {0}".format(e))
