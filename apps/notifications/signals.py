from datetime import datetime, timedelta

from dateutil.tz import *
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.appointments.models import Appointment, HealthPackageAppointment
from apps.appointments.views import (CancelMyAppointment, CreateMyAppointment,
                                     ReBookDoctorAppointment)
from apps.lab_and_radiology_items.models import (HomeCollectionAppointment,
                                                 PatientServiceAppointment)
from apps.patients.models import FamilyMember, Patient
from apps.reports.models import Report

from .serializers import MobileNotificationSerializer
from .tasks import send_push_notification
from .utils import cancel_parameters, doctor_rebook_parameters

@receiver(post_save, sender=FamilyMember)
def rebook_appointment_for_family_member(sender, instance, created, **kwargs):
    if not created:
        if instance._uhid_updated:
            appointments = instance.family_appointment.all().filter(
                appointment_date__gte=datetime.today().date(), status=1, payment_status__isnull=True)
            for appointment in appointments:
                param = dict()
                param["appointment_identifier"] = appointment.appointment_identifier
                param["reason_id"] = "1"
                param["status"] = "6"
                request_param = cancel_parameters(param)
                response = CancelMyAppointment.as_view()(request_param)
                if response.status_code == 200:
                    request_param = doctor_rebook_parameters(appointment)
                    response = ReBookDoctorAppointment.as_view()(request_param)
    return


@receiver(post_save, sender=Patient)
def rebook_appointment_for_patient(sender, instance, created, **kwargs):
    if not created:
        if instance._uhid_updated:
            appointments = instance.patient_appointment.all().filter(family_member__isnull=True,
                                                                     appointment_date__gte=datetime.today().date(), status=1, payment_status__isnull=True)
            for appointment in appointments:
                param = dict()
                param["appointment_identifier"] = appointment.appointment_identifier
                param["reason_id"] = "1"
                param["status"] = "6"
                request_param = cancel_parameters(param)
                response = CancelMyAppointment.as_view()(request_param)
                if response.status_code == 200:
                    request_param = doctor_rebook_parameters(appointment)
                    response = ReBookDoctorAppointment.as_view()(request_param)
    return
