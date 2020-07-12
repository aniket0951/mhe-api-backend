from datetime import datetime, timedelta

from django.conf import settings
from django.core.management import call_command

from apps.appointments.models import Appointment, HealthPackageAppointment
from apps.appointments.views import CancelMyAppointment
from apps.lab_and_radiology_items.models import (HomeCollectionAppointment,
                                                 PatientServiceAppointment)
from apps.patients.models import FamilyMember, Patient
from celery.schedules import crontab
from fcm_django.models import FCMDevice
from manipal_api.celery import app
from pyfcm import FCMNotification

from .serializers import MobileNotificationSerializer
from .utils import cancel_parameters


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
            "title": notification_instance.title, "message": notification_instance.message, "notification_type": notification_data["notification_type"], "appointment_id": notification_data["appointment_id"]}, low_priority=False)


@app.task(bind=True, name="silent_push_notification")
def send_silent_push_notification(self, **kwargs):
    fcm = FCMNotification(api_key=settings.FCM_API_KEY)
    notification_data = kwargs["notification_data"]
    if notification_data.get("patient"):
        patient_instance = Patient.objects.filter(
            id=notification_data.get("patient")["id"]).first()
        if patient_instance and patient_instance.device and patient_instance.device.token:
            result = fcm.notify_single_device(registration_id=patient_instance.device.token, data_message={
                                              "notification_type": "SILENT_NOTIFICATION", "appointment_id": notification_data["appointment_id"]}, low_priority=False)


@app.task(name="tasks.appointment_next_day_reminder_scheduler")
def appointment_next_day_reminder_scheduler():
    now = datetime.today() + timedelta(hours=24)
    appointments = Appointment.objects.filter(
        appointment_date=now.date(), status="1")
    for appointment_instance in appointments:
        notification_data = {}
        notification_data["title"] = "Reminder: Doctor Appointment"
        user_message = "Reminder: You have an appointment with {0}, {1}, {2}, tomorrow at {3}. For assistance, call Appointment Helpline 1800 102 5555.".format(
            appointment_instance.doctor.name, appointment_instance.department.name, appointment_instance.hospital.address, appointment_instance.appointment_slot)
        notification_data["message"] = user_message
        notification_data["notification_type"] = "GENERAL_NOTIFICATION"
        notification_data["appointment_id"] = appointment_instance.appointment_identifier
        if appointment_instance.family_member:
            member = FamilyMember.objects.filter(
                id=appointment_instance.family_member.id, patient_info_id=appointment_instance.patient.id).first()
            if Patient.objects.filter(uhid_number__isnull=False, uhid_number=member.uhid_number).exists():
                patient_member = Patient.objects.filter(
                    uhid_number=member.uhid_number).first()
                notification_data["recipient"] = patient_member.id
                send_push_notification.delay(
                    notification_data=notification_data)
        notification_data["recipient"] = appointment_instance.patient.id
        send_push_notification.delay(notification_data=notification_data)


@app.task(name="tasks.health_package_next_day_appointment_reminder")
def health_package_next_day_appointment_reminder():
    now = datetime.today() + timedelta(hours=24)
    appointments = HealthPackageAppointment.objects.filter(
        appointment_date__date=now.date(), appointment_status="Booked")
    for appointment_instance in appointments:
        notification_data = {}
        patient = Patient.objects.filter(
            id=appointment_instance.patient.id).first()
        notification_data["title"] = "Reminder: Health Package Appointment Reminder"
        notification_data["message"] = "Reminder: You have a Health Check appointment appointment at {0}, tomorrow at {1}. For assistance, call Appointment Helpline 1800 102 5555.".format(
            appointment_instance.hospital.address, appointment_instance.appointment_date.time())
        notification_data["notification_type"] = "GENERAL_NOTIFICATION"
        notification_data["appointment_id"] = appointment_instance.appointment_identifier
        if appointment_instance.family_member:
            member = FamilyMember.objects.filter(
                id=appointment_instance.family_member.id, patient_info_id=appointment_instance.patient.id).first()
            if Patient.objects.filter(uhid_number__isnull=False, uhid_number=member.uhid_number).exists():
                patient_member = Patient.objects.filter(
                    uhid_number=member.uhid_number).first()
                notification_data["recipient"] = patient_member.id
                send_push_notification.delay(
                    notification_data=notification_data)
        notification_data["recipient"] = patient.id
        send_push_notification.delay(notification_data=notification_data)


@app.task(name="tasks.health_package_appointment_reminder")
def health_package_appointment_reminder():
    now = datetime.today()
    appointments = HealthPackageAppointment.objects.filter(
        appointment_date__date=now.date(), appointment_status="Booked")
    for appointment_instance in appointments:
        notification_data = {}
        patient = Patient.objects.filter(
            id=appointment_instance.patient.id).first()
        notification_data["title"] = "Reminder: Health Package Appointment Reminder"
        notification_data["message"] = "Reminder: You have a Health Check appointment appointment at {0}, today at {1}. For assistance, call Appointment Helpline 1800 102 5555.".format(
            appointment_instance.hospital.address, appointment_instance.appointment_date.time())
        notification_data["notification_type"] = "GENERAL_NOTIFICATION"
        notification_data["appointment_id"] = appointment_instance.appointment_identifier
        if appointment_instance.family_member:
            member = FamilyMember.objects.filter(
                id=appointment_instance.family_member.id, patient_info_id=appointment_instance.patient.id).first()
            if Patient.objects.filter(uhid_number__isnull=False, uhid_number=member.uhid_number).exists():
                patient_member = Patient.objects.filter(
                    uhid_number=member.uhid_number).first()
                notification_data["recipient"] = patient_member.id
                send_push_notification.delay(
                    notification_data=notification_data)
        notification_data["recipient"] = patient.id
        send_push_notification.delay(notification_data=notification_data)


@app.task(name="tasks.appointment_reminder")
def appointment_reminder_scheduler():
    now = datetime.today()
    appointments = Appointment.objects.filter(
        appointment_date=now.date(), status="1")
    for appointment_instance in appointments:
        notification_data = {}
        notification_data["title"] = "Reminder: Doctor Appointment"
        user_message = "Reminder: You have an appointment with {0}, {1}, {2}, today at {3}. For assistance, call Appointment Helpline 1800 102 5555.".format(
            appointment_instance.doctor.name, appointment_instance.department.name, appointment_instance.hospital.address, appointment_instance.appointment_slot)
        notification_data["message"] = user_message
        notification_data["notification_type"] = "GENERAL_NOTIFICATION"
        notification_data["appointment_id"] = appointment_instance.appointment_identifier
        if appointment_instance.family_member:
            member = FamilyMember.objects.filter(
                id=appointment_instance.family_member.id, patient_info_id=appointment_instance.patient.id).first()
            if Patient.objects.filter(uhid_number__isnull=False, uhid_number=member.uhid_number).exists():
                patient_member = Patient.objects.filter(
                    uhid_number=member.uhid_number).first()
                notification_data["recipient"] = patient_member.id
                send_push_notification.delay(
                    notification_data=notification_data)
        notification_data["recipient"] = appointment_instance.patient.id
        send_push_notification.delay(notification_data=notification_data)


@app.task(name="tasks.auto_appointment_cancellation")
def auto_appointment_cancellation():
    now = datetime.now()
    end_time = now - timedelta(minutes=15)
    start_time = now - timedelta(hours=1, minutes=15)
    appointments = Appointment.objects.filter(
        created_at__date=now.date(), status="1", appointment_mode="VC", payment_status=None, booked_via_app=True).filter(created_at__time__gte=start_time, created_at__time__lte=end_time)
    for appointment in appointments:
        param = dict()
        param["appointment_identifier"] = appointment.appointment_identifier
        param["reason_id"] = "1"
        param["status"] = "2"
        request_param = cancel_parameters(param)
        response = CancelMyAppointment.as_view()(request_param)


@app.task(name="tasks.daily_auto_appointment_cancellation")
def daily_auto_appointment_cancellation():
    now = datetime.now() - timedelta(days=1)
    appointments = Appointment.objects.filter(
        created_at__date=now.date(), status="1", appointment_mode="VC", payment_status=None, booked_via_app=True)

    for appointment in appointments:
        param = dict()
        param["appointment_identifier"] = appointment.appointment_identifier
        param["reason_id"] = "1"
        param["status"] = "2"
        request_param = cancel_parameters(param)
        response = CancelMyAppointment.as_view()(request_param)


@app.task(name="tasks.daily_update")
def daily_update_scheduler():
    call_command("create_or_update_departments", verbosity=0)
    call_command("create_or_update_doctors", verbosity=0)
    call_command("create_or_update_health_packages", verbosity=0)
    call_command("create_or_update_lab_and_radiology_items", verbosity=0)
    call_command("update_doctors_profile", verbosity=0)


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
    },
    "daily_update_scheduler": {
        "task": "tasks.daily_update",
        "schedule": crontab(minute="0", hour="0")
    },
    "hourly_auto_cancellation_for_unpaid_vc_appointment": {
        "task": "tasks.auto_appointment_cancellation",
        "schedule": crontab(minute="15", hour="*")
    },
    "vc_daily_auto_appointment_cancellation": {
        "task": "tasks.daily_auto_appointment_cancellation",
        "schedule": crontab(minute="0", hour="3")
    }
}
