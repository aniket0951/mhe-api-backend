import json
import os

from django.core.files import File
from django.core.management import BaseCommand, CommandError
from tablib import Dataset

from apps.master_data.resources import BillingGroupResource


class Command(BaseCommand):
    help = "Create Billing Group"

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str)

    def handle(self, *args, **options):

        if options['file'] == None:
            raise CommandError(
                "Option `--file=<master_data_billing_group_file _path>` must be specified.")

        try:
            if not os.path.isfile(os.path.abspath(options['file'])):
                print("--file does not exists.")
                exit()
            if not options['file'].endswith('.csv'):
                print("--file should be a csv file.")
                exit()

            app_file = open(os.path.abspath(options['file']), 'rb')
            new_billing_groups = File(app_file)

            billing_group_resource = BillingGroupResource()
            dataset = Dataset()
            imported_data = dataset.load(
                new_billing_groups.read().decode('utf-8'), format='csv')
            result = billing_group_resource.import_data(
                dataset, dry_run=True)  # Test the data import

            if not result.has_errors():
                billing_group_resource.import_data(
                    dataset, dry_run=False)  # Actually import now
                print("Billing Group imported successfullly!")
            else:
                print("Unable to import Billing Group data!")

        except Exception as e:
            print(
                "Unexpected error occurred while import Billing Group - {0}".format(e))
