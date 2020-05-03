from rest_framework.test import APIRequestFactory
from apps.health_packages.models import HealthPackage
from datetime import datetime

def cancel_parameters(param, factory=APIRequestFactory()):
    return factory.post(
        '', param, format='json')

def rebook_parameters(instance, factory=APIRequestFactory()):
    param = dict()
    user = instance.patient
    date = datetime.combine(instance.appointment_date, instance.appointment_slot)
    date = date.strftime('%Y%m%d%H%M%S')
    if instance.family_member:
        user = instance.family_member
    param['doctor_code'] = instance.doctor.code
    param['appointment_date_time']=date
    param['location_code'] = instance.hospital.code
    param['patient_name'] = user.first_name
    param['mobile'] = str(user.mobile)
    param['email'] = str(user.email)
    param['speciality_code'] = instance.department.code
    param["mrn"] = user.uhid_number
    param["appointment_type"] = "NEW"
    return factory.post(
        '', param, format='json')



