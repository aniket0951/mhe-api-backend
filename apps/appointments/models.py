from django.db import models

from apps.doctors.models import Doctor
from apps.master_data.models import Hospital
from apps.users.models import BaseUser

# Create your models here.


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
    time_slot_from = models.TimeField()
    appointmentIdentifier = models.IntegerField()
    status = models.PositiveSmallIntegerField(choices=STATUS_CODES)
    req_patient = models.ForeignKey(
        BaseUser, on_delete=models.PROTECT, related_name='req_patient')
    doctor = models.ForeignKey(
        Doctor, on_delete=models.PROTECT, related_name='doctor')
    hospital = models.ForeignKey(
        Hospital, on_delete=models.PROTECT, related_name='hospital')
