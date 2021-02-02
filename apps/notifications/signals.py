from datetime import datetime

from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.appointments.views import (CancelMyAppointment,
                                     ReBookDoctorAppointment)
from apps.patients.models import FamilyMember, Patient
from .utils import cancel_parameters, doctor_rebook_parameters

@receiver(post_save, sender=FamilyMember)
def rebook_appointment_for_family_member(sender, instance, created, **kwargs):
    if not created and instance._uhid_updated:
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
                ReBookDoctorAppointment.as_view()(request_param)


@receiver(post_save, sender=Patient)
def rebook_appointment_for_patient(sender, instance, created, **kwargs):
    if not created and instance._uhid_updated:
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
                ReBookDoctorAppointment.as_view()(request_param)
