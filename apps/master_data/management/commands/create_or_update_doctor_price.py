import warnings
warnings.filterwarnings("ignore")
from django.core.management import BaseCommand

from apps.doctors.models import Doctor, DoctorCharges
from datetime import datetime
from apps.doctors.serializers import DoctorChargesSerializer

class Command(BaseCommand):
    help = "Create or Update Doctor Price"

    def handle(self, *args, **options):
        try:
            all_doctors = Doctor.objects.all()
            
            for each_doctor in all_doctors:
                DoctorChargesSerializer.get_and_update_doctor_price(each_doctor)
                    
            today_date = datetime.now().date()
            DoctorCharges.objects.filter(updated_at__date__lt=today_date).delete()
        except Exception as e:
            print("Unexpected error occurred while loading doctors- {0}".format(e))
