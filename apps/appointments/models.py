from datetime import datetime, timedelta

from django.db import models

from apps.doctors.models import Doctor
from apps.health_packages.models import HealthPackage
from apps.master_data.models import Hospital
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
    COMPLETED =4
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
                                      related_name='family_appointment', blank=True,
                                      null=True)
    doctor = models.ForeignKey(
        Doctor, on_delete=models.PROTECT, related_name='doctor_appointment')
    hospital = models.ForeignKey(
        Hospital, on_delete=models.PROTECT, related_name='hospital_appointment')
    reason = models.ForeignKey(
        CancellationReason, on_delete=models.PROTECT, related_name='cancellation_reason_appointment', null=True, blank=True)
    payment_status = models.CharField(max_length=10,
                                      blank=True,
                                      null=True)
    uhid = models.CharField(max_length=20,
                            blank=True,
                            null=True)
    booked_via_app = models.BooleanField(default=True)

    @property
    def is_cancellable(self):
        now = datetime.now() + timedelta(hours=5, minutes=30)
        if self.appointment_date > now.date():
            return True
        return False
    
    def save(self, *args, **kwargs):
        create_task = False 
        if self.pk is None:
            create_task = True 

        super(Appointment, self).save(*args, **kwargs)

        if create_task:
            schedule_time = datetime.combine(self.appointment_date, self.appointment_slot) - timedelta(hours=5, minutes=30)
            set_status_as_completed.apply_async(args=[self.appointment_identifier], eta=schedule_time)


class HealthPackageAppointment(models.Model):

    appointment_date = models.DateField(blank=True, null=True)
    appointment_slot = models.TimeField(blank=True, null=True)
    appointment_identifier = models.CharField(max_length=20,
                                              blank=True,
                                              null=True)
    appointment_status = models.CharField(max_length=10,
                                          default="Not Booked")
    payment = models.ForeignKey('payments.Payment', on_delete=models.PROTECT)
    health_package = models.ForeignKey(HealthPackage, on_delete=models.PROTECT)
    hospital = models.ForeignKey(
        Hospital, on_delete=models.PROTECT, related_name='hospital_health_appointment')
    reason = models.ForeignKey(CancellationReason, on_delete=models.PROTECT,
                               related_name='cancellation_reason_health_appointment',
                               null=True, blank=True)
    booked_via_app = models.BooleanField(default=True)

    @property
    def is_cancellable(self):
        if self.appointment_date:
            now = datetime.now() + timedelta(hours=5, minutes=30)
            if self.appointment_date > now.date():
                return True
        return False
