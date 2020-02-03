from django.db import models
from apps.patients.models import Patient
from apps.doctors.models import Doctor
from apps.master_data.models import Hospital

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
    token_no = models.IntegerField()
    status = models.PositiveSmallIntegerField(choices=STATUS_CODES)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    

