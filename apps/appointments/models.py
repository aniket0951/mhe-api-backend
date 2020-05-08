from datetime import datetime, timedelta

from django.contrib.postgres.fields import JSONField
from django.db import models

from apps.doctors.models import Doctor
from apps.health_packages.models import HealthPackage
from apps.master_data.models import Department, Hospital
from apps.patients.models import FamilyMember, Patient

from .tasks import set_status_as_completed


class CancellationReason(models.Model):

    reason = models.TextField(blank=False,
                              null=False,
                              max_length=100)


class Appointment(models.Model):
    CONFIRMED = 1
    CANCELLED = 2
    WAITING = 3
    COMPLETED = 4
    STATUS_CODES = (
        (CONFIRMED, 'Confirmed'),
        (CANCELLED, 'Cancelled'),
        (WAITING, 'Waiting'),
        (COMPLETED, 'Completed'),
    )
    appointment_date = models.DateField()
    appointment_slot = models.TimeField()
    appointment_identifier = models.CharField(max_length=20,
                                              blank=True,
                                              null=True)
    status = models.PositiveSmallIntegerField(choices=STATUS_CODES)
    patient = models.ForeignKey(
        Patient, on_delete=models.PROTECT, related_name='patient_appointment')

    family_member = models.ForeignKey(FamilyMember, on_delete=models.PROTECT,
                                      related_name='family_appointment',
                                      blank=True, null=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT,
                               related_name='doctor_appointment')

    hospital = models.ForeignKey(
        Hospital, on_delete=models.PROTECT, related_name='hospital_appointment')

    department = models.ForeignKey(Department, on_delete=models.PROTECT,
                                   related_name='hospital_department',
                                   blank=True, null=True)

    reason = models.ForeignKey(CancellationReason, on_delete=models.PROTECT,
                               related_name='cancellation_reason_appointment',
                               null=True, blank=True)

    payment_status = models.CharField(max_length=10,
                                      blank=True,
                                      null=True)
    uhid = models.CharField(max_length=20,
                            blank=True,
                            null=True)
    consultation_amount = models.FloatField(default=0,
                                            null=True)
    booked_via_app = models.BooleanField(default=True)

    @property
    def is_cancellable(self):
        if self.appointment_date:
            if ((self.appointment_date > datetime.now().date()) and (self.status == 1)):
                return True
        return False


class HealthPackageAppointment(models.Model):

    appointment_date = models.DateTimeField(blank=True, null=True)

    appointment_identifier = models.CharField(max_length=20,
                                              blank=True,
                                              null=True)

    appointment_status = models.CharField(max_length=10,
                                          default="Not Booked")

    patient = models.ForeignKey(Patient, on_delete=models.PROTECT,
                                related_name='patient_health_package_appointment')

    family_member = models.ForeignKey(FamilyMember, on_delete=models.PROTECT,
                                      related_name='family_health_package_appointment', blank=True,
                                      null=True)

    health_package = models.ManyToManyField(HealthPackage,
                                            blank=True,
                                            null=True
                                            )
    health_package_original = JSONField(null=True, blank=True)

    payment = models.ForeignKey('payments.Payment', on_delete=models.PROTECT,
                                related_name='payment_health_package_appointment',
                                blank=True, null=True)

    hospital = models.ForeignKey(Hospital, on_delete=models.PROTECT,
                                 related_name='hospital_health_appointment')

    reason = models.ForeignKey(CancellationReason, on_delete=models.PROTECT,
                               related_name='cancellation_reason_health_appointment',
                               null=True, blank=True)

    booked_via_app = models.BooleanField(default=True)

    @property
    def is_cancellable(self):
        if self.appointment_date:
            if ((self.appointment_date > datetime.now()) and (self.appointment_status != "Cancelled")):
                return True
        return False
