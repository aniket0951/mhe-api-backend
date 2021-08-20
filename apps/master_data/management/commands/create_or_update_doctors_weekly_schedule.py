import warnings
warnings.filterwarnings("ignore")
from django.core.management import BaseCommand
from apps.master_data.utils import MasterDataUtils

from apps.doctors.models import Doctor, DoctorsWeeklySchedule
from datetime import datetime

class Command(BaseCommand):
    help = "Create or Update Doctor Weekly Schedule"

    def handle(self, *args, **options):
        try:
            all_doctors = Doctor.objects.all()
            
            for each_doctor in all_doctors:
                MasterDataUtils.get_and_update_doctors_weekly_schedule(each_doctor)
                    
            today_date = datetime.now().date()
            DoctorsWeeklySchedule.objects.filter(updated_at__date__lt=today_date).delete()
        except Exception as e:
            print("Unexpected error occurred while loading doctors- {0}".format(e))