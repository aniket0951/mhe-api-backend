from datetime import datetime

from apps.health_packages.models import HealthPackage
from rest_framework.test import APIRequestFactory


def cancel_parameters(param, factory=APIRequestFactory()):
    return factory.post(
        '', param, format='json')


def doctor_rebook_parameters(instance, new_date=None, factory=APIRequestFactory()):
    param = dict()
    user = instance.patient
    date = datetime.combine(instance.appointment_date,
                            instance.appointment_slot)
    date = date.strftime('%Y%m%d%H%M%S')
    rescheduled = False
    if new_date:
        date = new_date
        rescheduled = True
    if instance.family_member:
        user = instance.family_member
    param['doctor_code'] = instance.doctor.code
    param['appointment_date_time'] = date
    param['location_code'] = instance.hospital.code
    param['patient_name'] = user.first_name
    param['mobile'] = str(user.mobile)
    param['email'] = str(user.email)
    param['speciality_code'] = instance.department.code
    param["mrn"] = user.uhid_number
    instance.pk = None
    instance.save()
    instance.appointment_identifier = "0000000"
    instance.uhid = user.uhid_number
    instance.reason = None
    instance.save()
    param["instance"] = instance.id
    param["rescheduled"] = rescheduled
    return factory.post(
        '', param, format='json')
