from datetime import datetime, timedelta

from dateutil.tz import *
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.appointments.models import Appointment, HealthPackageAppointment
from apps.appointments.views import CancelMyAppointment, CreateMyAppointment,RescheduleDoctorAppointment
from apps.lab_and_radiology_items.models import (HomeCollectionAppointment,
                                                 PatientServiceAppointment)
from apps.patients.models import FamilyMember, Patient
from apps.reports.models import Report

from .serializers import MobileNotificationSerializer
from .tasks import send_push_notification
from .utils import cancel_parameters,rebook_parameters



@receiver(post_save, sender=Appointment)
def send_new_appointment_notification(sender, **kwargs):
    appointment_instance = kwargs['instance']
    notification_data = {}
    if kwargs["created"]:
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
                notification_data["title"] = "Doctor Appointment Booked Successfully"
                notification_data["message"] = user_message
                send_push_notification.delay(notification_data=notification_data)
        notification_data["recipient"] = appointment_instance.patient.id
        notification_data["title"] = "Doctor Appointment Booked Successfully"
        notification_data["message"] = user_message
        send_push_notification.delay(notification_data=notification_data)


@receiver(post_save, sender=Report)
def send_new_report_notification(sender, **kwargs):
    new_report = kwargs['instance']
    notification_data = {}
    if kwargs["created"]:
        patient = Patient.objects.filter(uhid_number=new_report.uhid).first()
        if patient:
            notification_data["recipient"] = patient.id
            notification_data["title"] = "Report is Created"
            notification_data["message"] = "Hey {0}, Your Report is Created".format(
                patient.first_name)
            send_push_notification.delay(notification_data=notification_data)


def send_new_health_package_appointment_notification(**kwargs):
    appointment_instance = kwargs['instance']
    notification_data = {}
    notification_data["title"] = "Health PackageAppointment Booked Successfully"
    if kwargs["created"]:
        user_message = ""
        if appointment_instance.payment.payment_done_for_family_member:
            patient = Patient.objects.filter(uhid_number=appointment_instance.payment.uhid_number).first()
            if patient:
                user_message = "Hi {0}, your health package appointment is booked on {1} at {2}".format(
                    patient.first_name, appointment_instance.appointment_date, appointment_instance.appointment_slot)
                notification_data["recipient"] = patient.id
                notification_data["message"] = user_message
                send_push_notification.delay(notification_data=notification_data)
        patient = Patient.objects.filter(id=appointment_instance.payment.patient.id).first()
        user_message = "Hi {0}, your health package appointment is booked on {1} at {2}".format(
            patient.first_name, appointment_instance.appointment_date, appointment_instance.appointment_slot)
        notification_data["recipient"] = patient.id
        notification_data["message"] = user_message
        send_push_notification.delay(notification_data=notification_data)


@receiver(post_save, sender=HomeCollectionAppointment)
def send_new_home_collection_appointment_notification(sender, **kwargs):
    appointment_instance = kwargs['instance']
    notification_data = {}
    notification_data["title"] = "Home Collection Appointment Booked Successfully"
    if kwargs["created"]:
        patient = Patient.objects.filter(id=appointment_instance.patient.id).first()
        if appointment_instance.family_member:
            member = FamilyMember.objects.filter(
                id=appointment_instance.family_member.id, patient_info_id=appointment_instance.patient.id).first()
            if Patient.objects.filter(uhid_number__isnull=False, uhid_number=member.uhid_number).exists():
                patient_member = Patient.objects.filter(uhid_number=member.uhid_number).first()
                notification_data["recipient"] = patient_member.id
                notification_data["message"] = "Hi {0},You have a home collection appointment on {1}".format(patient_member.first_name,appointment_instance.appointment_date)
                send_push_notification.delay(notification_data=notification_data)
        notification_data["recipient"] = patient.id
        notification_data["message"] = "Hi {0},You have a home collection appointment on {1}".format(patient.first_name, appointment_instance.appointment_date)
        send_push_notification.delay(notification_data=notification_data)


# @receiver(post_save, sender=PatientServiceAppointment)
def send_new_patient_service_appointment_notification(sender, **kwargs):
    appointment_instance = kwargs['instance']
    notification_data = {}
    notification_data["title"] = "Service Appointment Booked Successfully"
    if kwargs["created"]:
        patient = Patient.objects.filter(
            id=appointment_instance.patient.id).first()
        if appointment_instance.family_member:
            member = FamilyMember.objects.filter(
                id=appointment_instance.family_member.id, patient_info_id=appointment_instance.patient.id).first()
            if Patient.objects.filter(uhid_number__isnull=False, uhid_number=member.uhid_number).exists():
                patient_member = Patient.objects.filter(
                    uhid_number=member.uhid_number).first()
                notification_data["recipient"] = patient_member.id
                notification_data["message"] = "Hi {0},You have a Service appointent on {1}".format(patient_member.first_name, appointment_instance.appointment_date)
                send_push_notification.delay(notification_data=notification_data)
        notification_data["recipient"] = patient.id
        notification_data["message"] = "Hi {0},You have a Service appointment on {1}".format(patient.first_name, appointment_instance.appointment_date)
        send_push_notification.delay(notification_data=notification_data)

# @receiver(post_save, sender=FamilyMember)
def rebook_appointment_for_family_member(sender,instance, created,**kwargs):
    if not created:
        if item == 'uhid_number':
            appointments = instance.family_appointment.all().filter(appointment_date__gte = datetime.today().date(), status = 1)
            for appointment in appointments:
                param = dict()
                param["appointment_identifier"] = appointment.appointment_identifier
                param["reason_id"] = "1"
                request_param = cancel_parameters(param)
                response = CancelMyAppointment.as_view()(request_param)
                if response.status_code == 200:
                    request_param = rebook_parameters(appointment)
                    RescheduleDoctorAppointment.as_view()(request_param)
    return

@receiver(post_save, sender=Patient)
def rebook_appointment_for_patient(sender, **kwargs):
    if not created:
        if item == 'uhid_number':
            appointments = instance.family_appointment.all().filter(appointment_date__gte = datetime.today().date(), status = 1)
            for appointment in appointments:
                param = dict()
                param["appointment_identifier"] = appointment.appointment_identifier
                param["reason_id"] = "1"
                request_param = cancel_parameters(param)
                response = CancelMyAppointment.as_view()(request_param)
                if response.status_code == 200:
                    request_param = rebook_parameters(appointment)
                    RescheduleDoctorAppointment.as_view()(request_param)
    return

                    