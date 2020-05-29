import urllib
from datetime import datetime

from django.conf import settings
from django.db.models import Q

from apps.appointments.models import Appointment
from apps.manipal_admin.models import ManipalAdmin
from apps.patients.models import Patient


def generate_pre_signed_url(image_url):
    try:
        decoded_url = urllib.request.unquote(image_url)
        url = settings.S3_CLIENT.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': decoded_url.split(settings.AWS_STORAGE_BUCKET_NAME+".s3.amazonaws.com/")[-1]
            }, ExpiresIn=600
        )
        return url
    except Exception:
        return None


def patient_user_object(request):
    try:
        return Patient.objects.get(id=request.user.id)
    except Exception as error:
        # logger.error("Unable to fetch patient user : " + str(error))
        return None


def manipal_admin_object(request):
    try:
        return ManipalAdmin.objects.get(id=request.user.id)
    except Exception as error:
        # logger.error("Unable to fetch patient user : " + str(error))
        return None


def get_appointment(patient_id):
    patient = Patient.objects.filter(id=patient_id).first()
    patient_appointment = Appointment.objects.filter(
        appointment_date__gte=datetime.now().date(), status=1).filter(
            (Q(uhid=patient.uhid_number) & Q(uhid__isnull=False)) | (Q(patient_id=patient.id) & Q(family_member__isnull=True)) | (Q(family_member_id__uhid_number__isnull=False) & Q(family_member_id__uhid_number=patient.patient.uhid_number)))
    family_members = patient.patient_family_member_info.filter(is_visible=True)
    for member in family_members:
        family_appointment = Appointment.objects.filter(
                    (Q(appointment_date__gt=datetime.now().date()) | (Q(appointment_date=datetime.now().date()) & Q(appointment_slot__gt=datetime.now().time()))) & Q(status=1)).filter(
                Q(family_member_id=member.id) | (Q(patient_id__uhid_number__isnull=False) & Q(patient_id__uhid_number=member.uhid_number)) | (Q(uhid__isnull=False) & Q(uhid=member.uhid_number)) | (Q(family_member_id__uhid_number__isnull=False) & Q(family_member_id__uhid_number=member.uhid_number)))
        patient_appointment = patient_appointment.union(family_appointment)
    return patient_appointment.order_by('appointment_date', 'appointment_slot')
