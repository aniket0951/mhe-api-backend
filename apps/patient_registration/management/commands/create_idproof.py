import json
import os

from django.core.files import File
from django.core.management import BaseCommand, CommandError
from tablib import Dataset

from apps.patient_registration.models import IDProof
from apps.patient_registration.resources import IDProofResource

class Command(BaseCommand):
    help = "Create IDProof"

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str)

    def handle(self, *args, **options):

        if options['file'] == None:
            raise CommandError(
                "Option `--file=<master_data_id_proof_resource_file _path>` must be specified.")

        try:
            if not os.path.isfile(os.path.abspath(options['file'])):
                print("--file does not exists.")
                exit()
            if not options['file'].endswith('.csv'):
                print("--file should be a csv file.")
                exit()

            app_file = open(os.path.abspath(options['file']), 'rb')
            new_id_proof_resources = File(app_file)

            id_proof_resource = IDProofResource()

            dataset = Dataset()
            dataset.load(
                new_id_proof_resources.read().decode('utf-8'), format='csv')
                
            result = id_proof_resource.import_data(
                dataset, dry_run=True)  # Test the data import

            if not result.has_errors():
                id_proof_resource.import_data(
                    dataset, dry_run=False)  # Actually import now
                print("IDProof imported successfully!")
            else:
                print("Unable to import IDProof data!")

        except Exception as e:
            print(
                "Unexpected error occurred while import IDProof - {0}".format(e))
