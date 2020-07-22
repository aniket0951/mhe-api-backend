import urllib
from datetime import datetime

from django.conf import settings
from django.db.models import Q

from apps.appointments.models import Appointment
from apps.manipal_admin.models import ManipalAdmin
from apps.patients.models import Patient
from rest_framework.serializers import ValidationError


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
    if not patient:
        raise ValidationError("Patient does not Exist")
    member_uhid = patient.uhid_number
    patient_appointment = Appointment.objects.filter(
        Q(appointment_date__gte=datetime.now().date()) & Q(status=1) & ((Q(uhid__isnull=False) & Q(uhid=member_uhid)) | (Q(patient_id=patient.id) & Q(family_member__isnull=True)))).exclude(
        Q(appointment_mode="VC") & (Q(vc_appointment_status="4") | Q(payment_status__isnull=True)))
    family_members = patient.patient_family_member_info.filter(is_visible=True)
    for member in family_members:
        member_uhid = member.uhid_number
        family_appointment = Appointment.objects.filter(
            Q(appointment_date__gte=datetime.now().date()) & Q(status=1) & ((Q(uhid__isnull=False) & Q(uhid=member_uhid)) | Q(family_member_id=member.id))).exclude(
            Q(appointment_mode="VC") & (Q(vc_appointment_status="4") | Q(payment_status__isnull=True)))
        patient_appointment = patient_appointment.union(family_appointment)
    return patient_appointment.order_by('appointment_date', 'appointment_slot')
