from datetime import datetime

from django.conf import settings

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
    param["instance"] = instance.id
    param["rescheduled"] = rescheduled
    return factory.post(
        '', param, format='json')

def get_birthday_notification_data(patient_id,users_first_name):
    notification_data = {}
    notification_data["title"] = "Wishing You A Very Happy Birthday"
    user_message = "Happy birthday, %s! I hope this is the begining of your greatest, most wonderful year ever!"%(str(users_first_name))
    notification_data["message"] = user_message
    notification_data["notification_type"] = "GENERAL_NOTIFICATION"
    notification_data["recipient"] = patient_id.id
    notification_data["notification_image_url"] = settings.BIRTHDAY_NOTIFICATION_IMAGE_URL
    return notification_data