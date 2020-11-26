import json
import os

from django.core.management import BaseCommand, CommandError

from apps.doctors.models import Doctor, DoctorCharges
from apps.doctors.serializers import DoctorChargesSerializer
from apps.master_data.models import Department, Hospital
from apps.master_data.resources import BillingGroupResource
from rest_framework.test import APIClient
from tablib import Dataset

client = APIClient()


class Command(BaseCommand):
    help = "Create or Update Doctor Price"

    def handle(self, *args, **options):
        try:
            all_doctors = Doctor.objects.all()
            print(all_doctors)
            for each_doctor in all_doctors:
                all_departments = each_doctor.hospital_departments.all()
                for each_department in all_departments:
                    data = dict()
                    location_code = each_doctor.hospital.code
                    doctor_code = each_doctor.code
                    data["doctor_info"] = each_doctor.id
                    data["department_info"] = each_department.department.id
                    response = client.post('/api/doctors/doctor_charges',
                                           json.dumps({'location_code': location_code, 'specialty_code': each_department.department.code, 'doctor_code': doctor_code}), content_type='application/json')
                    consultation_charge = response.data["data"]
                    if response.status_code == 200 and response.data["success"] == True:
                        data["hv_consultation_charges"] = consultation_charge["hv_charge"]
                        data["vc_consultation_charges"] = consultation_charge["vc_charge"]
                        data["pr_consultation_charges"] = consultation_charge["pr_charge"]
                        doctor_instance = DoctorCharges.objects.filter(
                            doctor_info__code=doctor_code, department_info__code=each_department.department.code).first()
                        if doctor_instance:
                            serializer = DoctorChargesSerializer(
                                doctor_instance, data=data, partial=True)
                        else:
                            serializer = DoctorChargesSerializer(data=data)
                        serializer.is_valid(raise_exception=True)
                        serializer.save()

        except Exception as e:
            print(
                "Unexpected error occurred while loading doctors- {0}".format(e))
