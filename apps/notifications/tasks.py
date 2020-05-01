from datetime import datetime, timedelta

from apps.appointments.models import Appointment, HealthPackageAppointment
from apps.lab_and_radiology_items.models import (HomeCollectionAppointment,
                                                 PatientServiceAppointment)
from apps.patients.models import FamilyMember, Patient
from celery.schedules import crontab
from fcm_django.models import FCMDevice
from manipal_api.celery import app
from manipal_api.settings import FCM_API_KEY
from pyfcm import FCMNotification

from .serializers import MobileNotificationSerializer


@app.task(bind=True, name="push_notifications")
def send_push_notification(self, **kwargs):
    notification_data = kwargs["notification_data"]
    fcm = FCMNotification(api_key=FCM_API_KEY)
    mobile_notification_serializer = MobileNotificationSerializer(
        data=notification_data)
    mobile_notification_serializer.is_valid(raise_exception=True)
    notification_instance = mobile_notification_serializer.save()
    if (hasattr(notification_instance.recipient, 'device') and notification_instance.recipient.device.token):
        result = fcm.notify_single_device(registration_id=notification_instance.recipient.device.token, data_message={
            "title": notification_instance.title, "message": notification_instance.message}, low_priority=False)


@app.task(name="tasks.appointment_reminder")
def appointment_reminder_scheduler():
    now = datetime.today()
    time_duration = now + timedelta(hours=12)
    if (now.date() != time_duration.date()):
        time_duration = now.replace(hour=23, minute=59)
    appointments = Appointment.objects.filter(appointment_date=now.date(
    ), appointment_slot__gte=now.time(), appointment_slot__lte=time_duration.time())
    for appointment_instance in appointments:
        notification_data = {}
        user_message = "Dear {0}, Your Appointment has been booked with {1} on {2} at {3} with appointment id:{4} at {5}".format(
            appointment_instance.patient.first_name, appointment_instance.doctor.name, appointment_instance.appointment_date, appointment_instance.appointment_slot, appointment_instance.appointment_identifier, appointment_instance.hospital.address)
        if appointment_instance.family_member:
            user_message = "Dear {0}, Your Appointment has been booked by {6} with {1} on {2} at {3} with appointment id:{4} at {5}".format(appointment_instance.family_member.first_name, appointment_instance.doctor.name,
                                                                                                                                            appointment_instance.appointment_date, appointment_instance.appointment_slot, appointment_instance.appointment_identifier, appointment_instance.hospital.address, appointment_instance.patient.first_name)
            member = FamilyMember.objects.filter(
                id=appointment_instance.family_member.id, patient_info_id=appointment_instance.patient.id).first()
            if Patient.objects.filter(uhid_number__isnull=False, uhid_number=member.uhid_number).exists():
                patient_member = Patient.objects.filter(
                    uhid_number=member.uhid_number).first()
                notification_data["recipient"] = patient_member.id
                notification_data["title"] = "Reminder: Doctor Appointment"
                notification_data["message"] = user_message
                schedule_time = datetime.combine(appointment_instance.appointment_date,
                                                 appointment_instance.appointment_slot) - timedelta(hours=7, minutes=30)
                notification_data["title"] = "Reminder: Doctor Appointment"
                send_push_notification.apply_async(
                    kwargs={"notification_data": notification_data}, eta=schedule_time)
        notification_data["recipient"] = appointment_instance.patient.id
        notification_data["title"] = "Reminder: Doctor Appointment"
        notification_data["message"] = user_message
        schedule_time = datetime.combine(appointment_instance.appointment_date,
                                         appointment_instance.appointment_slot) - timedelta(hours=7, minutes=30)
        send_push_notification.apply_async(
            kwargs={"notification_data": notification_data}, eta=schedule_time)


@app.task(name="tasks.home_collection_appointment_reminder")
def home_collection_appointment_reminder():
    now = datetime.today()
    time_duration = now + timedelta(hours=12)
    appointments = HomeCollectionAppointment.objects.filter(appointment_date__gte=now,
                                                            appointment_date__lte=time_duration)
    for appointment_instance in appointments:
        notification_data = {}
        patient = Patient.objects.filter(
            id=appointment_instance.patient.id).first()
        notification_data["title"] = "Reminder: Home collection Appointment"
        notification_data["message"] = "Hi {0},You have a home collection appointment today at {1}".format(
            patient.first_name, appointment_instance.appointment_date.time())
        schedule_time = appointment_instance.appointment_date - \
            timedelta(hours=7, minutes=30)
        if appointment_instance.family_member:
            member = FamilyMember.objects.filter(
                id=appointment_instance.family_member.id, patient_info_id=appointment_instance.patient.id).first()
            if Patient.objects.filter(uhid_number__isnull=False, uhid_number=member.uhid_number).exists():
                patient_member = Patient.objects.filter(
                    uhid_number=member.uhid_number).first()
                notification_data["recipient"] = patient_member.id
                notification_data["message"] = "Hi {0},You have a home collection appointment today at {1}".format(
                    patient_member.first_name, appointment_instance.appointment_date.time())
                send_push_notification.apply_async(
                    kwargs={"notification_data": notification_data}, eta=schedule_time)
        notification_data["recipient"] = patient.id
        send_push_notification.apply_async(
            kwargs={"notification_data": notification_data}, eta=schedule_time)


@app.task(name="tasks.patient_service_reminder")
def patient_service_reminder():
    now = datetime.today()
    appointments = HomeCollectionAppointment.objects.filter(
        appointment_date=now.date())
    for appointment_instance in appointments:
        notification_data = {}
        notification_data["title"] = "Reminder: Patient service Appointment"
        patient = Patient.objects.filter(
            id=appointment_instance.patient.id).first()
        notification_data["message"] = "Hi {0},have a service appointment today".format(
            patient.first_name)
        if appointment_instance.family_member:
            member = FamilyMember.objects.filter(
                id=appointment_instance.family_member.id, patient_info_id=appointment_instance.patient.id).first()
            if Patient.objects.filter(uhid_number__isnull=False, uhid_number=member.uhid_number).exists():
                patient_member = Patient.objects.filter(
                    uhid_number=member.uhid_number).first()
                notification_data["recipient"] = patient_member.id
                notification_data["message"] = "Hi {0},You have a Service appointment today".format(
                    appointment_instance.patient_member.first_name)
                send_push_notification.delay(
                    notification_data=notification_data)
        notification_data["recipient"] = patient.id
        send_push_notification.delay(notification_data=notification_data)


app.conf.beat_schedule = {
    "appointment_reminder": {
        "task": "tasks.appointment_reminder",
        "schedule": crontab(minute="0", hour='*/12')
    },
    "health_package_appointment_reminder": {
        "task": "tasks.home_collection_appointment_reminder",
        "schedule": crontab(minute="0", hour='*/12')
    },
    "patient_service_reminder": {
        "task": "tasks.patient_service_reminder",
        "schedule": crontab(minute="0", hour="0")
    }

}
