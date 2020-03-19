from django.db import models

from apps.doctors.models import Doctor
from apps.master_data.models import Hospital
from apps.patients.models import FamilyMember, Patient


class CancellationReason(models.Model):

    reason = models.TextField(blank=False,
                              null=False,
                              max_length=100)


class Appointment(models.Model):
    CONFIRMED = 1
    CANCELLED = 2
    WAITING = 3
    STATUS_CODES = (
        (CONFIRMED, 'Confirmed'),
        (CANCELLED, 'Cancelled'),
        (WAITING, 'Waiting'),
    )
    appointment_date = models.DateField()
    appointment_slot = models.TimeField()
    appointment_identifier = models.CharField(max_length=20,
                                              blank=True,
                                              null=True)
    status = models.PositiveSmallIntegerField(choices=STATUS_CODES)
    patient = models.ForeignKey(
        Patient, on_delete=models.PROTECT, related_name='patient_appointment')
    family_member = models.ForeignKey(FamilyMember, on_delete=models.PROTECT, related_name='family_appointment', blank=True,
                                      null=True)
    doctor = models.ForeignKey(
        Doctor, on_delete=models.PROTECT, related_name='doctor_appointment')
    hospital = models.ForeignKey(
        Hospital, on_delete=models.PROTECT, related_name='hospital_appointment')
    reason = models.ForeignKey(
        CancellationReason, on_delete=models.PROTECT, related_name='cancellation_reason_appointment', null=True, blank=True)
    payment_status =  models.CharField(max_length=10,
                                    blank = True,
                                    null = True)
