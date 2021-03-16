from datetime import datetime, timedelta

import logging

from django.conf import settings
from django.core.management import call_command
from pushjack import APNSClient

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

NOTIFICAITON_TYPE_MAP = {
    "HOLD_VC_NOTIFICATION":"2"
}

_logger = logging.getLogger("Django")

@app.task(bind=True, name="push_notifications")
def send_push_notification(self, **kwargs):
    notification_data = kwargs["notification_data"]
    mobile_notification_serializer = MobileNotificationSerializer(
        data=notification_data)
    mobile_notification_serializer.is_valid(raise_exception=True)
    notification_instance = mobile_notification_serializer.save()
    recipient = notification_instance.recipient
    if (hasattr(recipient, 'device') and recipient.device.token):
        if recipient.device.platform == 'Android':
            fcm = FCMNotification(api_key=settings.FCM_API_KEY)
            if notification_data.get("doctor_name"):
                fcm.notify_single_device(registration_id=notification_instance.recipient.device.token, data_message={
                    "title": notification_instance.title, "message": notification_instance.message, "notification_type": notification_data["notification_type"], "appointment_id": notification_data["appointment_id"], "doctor_name": notification_data["doctor_name"]}, low_priority=False)
            else:
                fcm.notify_single_device(registration_id=notification_instance.recipient.device.token, data_message={
                    "title": notification_instance.title, "message": notification_instance.message, "notification_type": notification_data["notification_type"], "appointment_id": notification_data["appointment_id"]}, low_priority=False)
        elif recipient.device.platform == 'iOS':
            client = APNSClient(certificate=settings.APNS_CERT_PATH)
            alert = notification_instance.message
            token = notification_instance.recipient.device.token
            _logger.info("notification_data.get(\"notification_type\") :%s"%(str(notification_data.get("notification_type"))))
            if notification_data.get("notification_type") in NOTIFICAITON_TYPE_MAP:
                _logger.info("notification_data.get(\"notification_type\") in NOTIFICAITON_TYPE_MAP :%s"%(str(notification_data.get("notification_type") in NOTIFICAITON_TYPE_MAP)))
            if notification_data.get("notification_type") and notification_data.get("notification_type") in NOTIFICAITON_TYPE_MAP and NOTIFICAITON_TYPE_MAP.get(notification_data.get("notification_type")):
                _logger.info("NOTIFICAITON_TYPE_MAP.get(notification_data.get(\"notification_type\")) :%s"%(str(NOTIFICAITON_TYPE_MAP.get(notification_data.get("notification_type")))))
            client.send(token,
                        alert,
                        badge=1,
                        sound="default",
                        extra={
                            'notification_type': NOTIFICAITON_TYPE_MAP[notification_data["notification_type"]] if notification_data.get("notification_type") and notification_data.get("notification_type") in NOTIFICAITON_TYPE_MAP and NOTIFICAITON_TYPE_MAP.get(notification_data.get("notification_type")) else '1',
                            'appointment_id': notification_data["appointment_id"]
                        }
                    )


@app.task(bind=True, name="silent_push_notification")
def send_silent_push_notification(self, **kwargs):
    fcm = FCMNotification(api_key=settings.FCM_API_KEY)
    notification_data = kwargs["notification_data"]
    if notification_data.get("patient"):
        patient_instance = Patient.objects.filter(
            id=notification_data.get("patient")["id"]).first()
        if (hasattr(patient_instance, 'device') and patient_instance.device.token):
            if patient_instance.device.platform == 'Android':
                fcm.notify_single_device(registration_id=patient_instance.device.token, data_message={
                    "notification_type": "SILENT_NOTIFICATION", "appointment_id": notification_data["appointment_id"]}, low_priority=False)
            elif patient_instance.device.platform == 'iOS':
                client = APNSClient(certificate=settings.APNS_CERT_PATH)
                token = patient_instance.device.token
                alert = "Doctor completed this consultation"
                client.send(token,
                                  alert,
                                  badge=1,
                                  sound="default",
                                  extra={'notification_type': '2',
                                         'appointment_id': notification_data["appointment_id"]
                                         }
                                  )


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
    end_time = now - timedelta(minutes=13)
    start_time = now - timedelta(minutes=45)
    appointments = Appointment.objects.filter(
        created_at__date=now.date(), status="1", appointment_mode="VC", payment_status=None, booked_via_app=True).filter(created_at__time__gte=start_time, created_at__time__lte=end_time)
    for appointment in appointments:
        param = dict()
        param["appointment_identifier"] = appointment.appointment_identifier
        param["reason_id"] = "1"
        param["status"] = "2"
        request_param = cancel_parameters(param)
        CancelMyAppointment.as_view()(request_param)


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
        CancelMyAppointment.as_view()(request_param)


@app.task(name="tasks.daily_update")
def daily_update_scheduler():
    call_command("generate_app_statistics", verbosity=0)
    call_command("create_or_update_departments", verbosity=0)
    call_command("create_or_update_doctors", verbosity=0)
    call_command("create_or_update_health_packages", verbosity=0)
    call_command("create_or_update_lab_and_radiology_items", verbosity=0)
    call_command("update_doctors_profile", verbosity=0)
    call_command("create_or_update_doctor_price", verbosity=0)
    call_command("update_health_package_image", verbosity=0)


@app.task(name="tasks.update_health_package")
def update_health_package():
    call_command("create_or_update_health_packages", verbosity=0)
    call_command("update_health_package_image", verbosity=0)


@app.task(name="tasks.update_doctor")
def update_doctor():
    call_command("create_or_update_doctors", verbosity=0)
    call_command("update_doctors_profile", verbosity=0)
    call_command("create_or_update_doctor_price", verbosity=0)


@app.task(name="tasks.update_item")
def update_item():
    call_command("create_or_update_lab_and_radiology_items", verbosity=0)


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
        "schedule": crontab(minute="0", hour="6")
    },
    "hourly_auto_cancellation_for_unpaid_vc_appointment": {
        "task": "tasks.auto_appointment_cancellation",
        "schedule": crontab(minute="*/15", hour="*")
    },
    "vc_daily_auto_appointment_cancellation": {
        "task": "tasks.daily_auto_appointment_cancellation",
        "schedule": crontab(minute="0", hour="3")
    }
}
