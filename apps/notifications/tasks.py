from datetime import datetime, timedelta

from celery.schedules import crontab
from django.conf import settings
from fcm_django.models import FCMDevice
from pyfcm import FCMNotification

from apps.appointments.models import Appointment, HealthPackageAppointment
from apps.lab_and_radiology_items.models import (HomeCollectionAppointment,
                                                 PatientServiceAppointment)
from apps.patients.models import FamilyMember, Patient
from manipal_api.celery import app

from .serializers import MobileNotificationSerializer


@app.task(bind=True, name="push_notifications")
def send_push_notification(self, **kwargs):
    notification_data = kwargs["notification_data"]
    fcm = FCMNotification(api_key=settings.FCM_API_KEY)
    mobile_notification_serializer = MobileNotificationSerializer(
        data=notification_data)
    mobile_notification_serializer.is_valid(raise_exception=True)
    notification_instance = mobile_notification_serializer.save()
    if (hasattr(notification_instance.recipient, 'device') and notification_instance.recipient.device.token):
        result = fcm.notify_single_device(registration_id=notification_instance.recipient.device.token, data_message={
            "title": notification_instance.title, "message": notification_instance.message}, low_priority=False)


@app.task(name="tasks.appointment_next_day_reminder_scheduler")
def appointment_next_day_reminder_scheduler():
    now = datetime.today() + timedelta(hours=24)
    appointments = Appointment.objects.filter(appointment_date=now.date(), status = "1")
    for appointment_instance in appointments:
        notification_data = {}
        notification_data["title"] = "Reminder: Doctor Appointment"
        user_message = "Reminder: You have an appointment with {0}, {1}, {2}, tomorrow at {3}. For assistance, call Appointment Helpline 1800 102 5555.".format(appointment_instance.doctor.name, appointment_instance.department.name, appointment_instance.hospital.address,appointment_instance.appointment_slot)
        notification_data["message"] = user_message
        if appointment_instance.family_member:
            member = FamilyMember.objects.filter(
                id=appointment_instance.family_member.id, patient_info_id=appointment_instance.patient.id).first()
            if Patient.objects.filter(uhid_number__isnull=False, uhid_number=member.uhid_number).exists():
                patient_member = Patient.objects.filter(
                    uhid_number=member.uhid_number).first()
                notification_data["recipient"] = patient_member.id
                send_push_notification.delay(notification_data=notification_data)
        notification_data["recipient"] = appointment_instance.patient.id
        send_push_notification.delay(notification_data=notification_data)

@app.task(name="tasks.health_package_next_day_appointment_reminder")
def health_package_next_day_appointment_reminder():
    now = datetime.today() + timedelta(hours=24)
    appointments = HealthPackageAppointment.objects.filter(appointment_date__date=now.date(), appointment_status="Booked")
    for appointment_instance in appointments:
        notification_data = {}
        patient = Patient.objects.filter(
            id=appointment_instance.patient.id).first()
        notification_data["title"] = "Reminder: Health Package Appointment Reminder"
        notification_data["message"] = "Reminder: You have a Health Check appointment appointment at {0}, tomorrow at {1}. For assistance, call Appointment Helpline 1800 102 5555.".format(
            appointment_instance.hospital.address, appointment_instance.appointment_date.time())
        if appointment_instance.family_member:
            member = FamilyMember.objects.filter(
                id=appointment_instance.family_member.id, patient_info_id=appointment_instance.patient.id).first()
            if Patient.objects.filter(uhid_number__isnull=False, uhid_number=member.uhid_number).exists():
                patient_member = Patient.objects.filter(
                    uhid_number=member.uhid_number).first()
                notification_data["recipient"] = patient_member.id
                send_push_notification.delay(notification_data=notification_data)
        notification_data["recipient"] = patient.id
        send_push_notification.delay(notification_data=notification_data)

@app.task(name="tasks.health_package_appointment_reminder")
def health_package_appointment_reminder():
    now = datetime.today()
    appointments = HealthPackageAppointment.objects.filter(appointment_date__date=now.date(), appointment_status="Booked")
    for appointment_instance in appointments:
        notification_data = {}
        patient = Patient.objects.filter(
            id=appointment_instance.patient.id).first()
        notification_data["title"] = "Reminder: Health Package Appointment Reminder"
        notification_data["message"] = "Reminder: You have a Health Check appointment appointment at {0}, today at {1}. For assistance, call Appointment Helpline 1800 102 5555.".format(
            appointment_instance.hospital.address, appointment_instance.appointment_date.time())
        if appointment_instance.family_member:
            member = FamilyMember.objects.filter(
                id=appointment_instance.family_member.id, patient_info_id=appointment_instance.patient.id).first()
            if Patient.objects.filter(uhid_number__isnull=False, uhid_number=member.uhid_number).exists():
                patient_member = Patient.objects.filter(
                    uhid_number=member.uhid_number).first()
                notification_data["recipient"] = patient_member.id
                send_push_notification.delay(notification_data=notification_data)
        notification_data["recipient"] = patient.id
        send_push_notification.delay(notification_data=notification_data)

@app.task(name="tasks.appointment_reminder")
def appointment_reminder_scheduler():
    now = datetime.today()
    appointments = Appointment.objects.filter(appointment_date=now.date(), status="1")
    for appointment_instance in appointments:
        notification_data = {}
        notification_data["title"] = "Reminder: Doctor Appointment"
        user_message = "Reminder: You have an appointment with {0}, {1}, {2}, today at {3}. For assistance, call Appointment Helpline 1800 102 5555.".format(appointment_instance.doctor.name, appointment_instance.department.name, appointment_instance.hospital.address,appointment_instance.appointment_slot)
        notification_data["message"] = user_message
        if appointment_instance.family_member:
            member = FamilyMember.objects.filter(
                id=appointment_instance.family_member.id, patient_info_id=appointment_instance.patient.id).first()
            if Patient.objects.filter(uhid_number__isnull=False, uhid_number=member.uhid_number).exists():
                patient_member = Patient.objects.filter(
                    uhid_number=member.uhid_number).first()
                notification_data["recipient"] = patient_member.id
                send_push_notification.delay(notification_data=notification_data)
        notification_data["recipient"] = appointment_instance.patient.id
        send_push_notification.delay(notification_data=notification_data)

  

app.conf.beat_schedule = {
    "appointment_reminder": {
        "task": "tasks.appointment_reminder",
        "schedule": crontab(minute="0", hour='6')
    },
    "health_package_appointment_reminder": {
        "task": "tasks.health_package_appointment_reminder",
        "schedule": crontab(minute="0", hour='6')
    },
    "health_package_next_day_appointment_reminder": {
        "task": "tasks.health_package_next_day_appointment_reminder",
        "schedule": crontab(minute="0", hour="18")
    },
    "appointment_next_day_reminder_scheduler": {
        "task": "tasks.appointment_next_day_reminder_scheduler",
        "schedule": crontab(minute="0", hour="18")
    }
}
