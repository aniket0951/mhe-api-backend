from manipal_api.celery import app
from .models import Appointment

@app.task
def set_status_as_completed(appointment_identifier):
    appointment_object = Appointment.objects.filter(appointment_identifier = appointment_identifier).first()
    if appointment_object.status == 1:
        appointment_object.status = 4 
        appointment_object.save()