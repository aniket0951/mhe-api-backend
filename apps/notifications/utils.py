import openpyxl
import re
from datetime import datetime
from django.conf import settings
from django.db.models.query_utils import Q
from apps.patients.models import FamilyMember, Patient
from rest_framework.test import APIRequestFactory

from apps.notifications.models import NotificationTemplate

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
    param["appointment_mode"] = instance.appointment_mode
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

def get_scheduler_notification_data(scheduler):
    notification_data = {}
    notification_data["title"] = scheduler.template_id.notification_subject
    notification_data["message"] = scheduler.template_id.notification_body
    notification_data["notification_type"] = "GENERAL_NOTIFICATION"
    return notification_data

def create_notification_template(notification_subject,notification_body):
    existing_notification_id = NotificationTemplate.objects.filter( 
                                                                Q(notification_subject=notification_subject) & 
                                                                Q(notification_body=notification_body)
                                                            ).first()                
    if existing_notification_id:
        return existing_notification_id.id
    else:
        new_notification_template_id = NotificationTemplate.objects.create(notification_subject=notification_subject,notification_body=notification_body)
        new_notification_template_id.save()
        return new_notification_template_id.id
            
def read_excel_file_data(excel_file):
    try:
        wb = openpyxl.load_workbook(filename=excel_file)
    
    except Exception as e:
        wb = openpyxl.Workbook()
        wb.save(excel_file)
        wb = openpyxl.load_workbook(filename=excel_file)
        
    ws = wb.active
    excel_data = list()
    for row in ws.iter_rows():
        row_data = list()
        for cell in row:
            row_data.append(str(cell.value))
        excel_data.append(row_data)

    uhid_list = [item for sublist in excel_data for item in sublist if item.startswith("MH")]
    uhid_string = format_and_clean_uhid(','.join(uhid_list))

    return uhid_string

def format_and_clean_uhid(uhid):
    if uhid:
        uhid = uhid.upper()
        pattern = re.compile(r'\s+')
        uhid = re.sub(pattern, '', uhid)
    return uhid

        