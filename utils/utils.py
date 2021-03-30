import logging
import urllib
from datetime import datetime, timedelta
from utils.exceptions import UserNotRegisteredException
from django.db.models import Count, Sum

from django.conf import settings
from django.db.models import Q

from apps.appointments.models import Appointment, HealthPackageAppointment
from apps.doctors.models import Doctor
from apps.lab_and_radiology_items.models import (HomeCollectionAppointment,
                                                 PatientServiceAppointment)
from apps.manipal_admin.models import ManipalAdmin
from apps.notifications.models import MobileDevice
from apps.patients.models import FamilyMember, Patient
from apps.payments.models import Payment
from rest_framework.serializers import ValidationError

logger = logging.getLogger('django')

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
        logger.error("Unable to fetch patient user : " + str(error))
        return None


def manipal_admin_object(request):
    try:
        if request.user and request.user.id:
            return ManipalAdmin.objects.get(id=request.user.id)
    except Exception as error:
        logger.error("Unable to fetch patient user : " + str(error))
    return None


def get_appointment(patient_id):
    patient = Patient.objects.filter(id=patient_id).first()
    if not patient:
        raise ValidationError("Patient does not Exist")
    member_uhid = patient.uhid_number
    if patient.active_view == 'Corporate':
        patient_appointment = Appointment.objects.filter(
        Q(appointment_date__gte=datetime.now().date()) & Q(status=1) & ((Q(uhid__isnull=False) & Q(uhid=member_uhid)) | (Q(patient_id=patient.id) & Q(family_member__isnull=True)))).exclude(
        Q(appointment_mode="VC") & (Q(vc_appointment_status="4") | Q(payment_status__isnull=True))).filter(corporate_appointment=True)
        return patient_appointment

    patient_appointment = Appointment.objects.filter(
        Q(appointment_date__gte=datetime.now().date()) & Q(status=1) & ((Q(uhid__isnull=False) & Q(uhid=member_uhid)) | (Q(patient_id=patient.id) & Q(family_member__isnull=True)))).exclude(
        Q(appointment_mode="VC") & (Q(vc_appointment_status="4") | Q(payment_status__isnull=True))).filter(corporate_appointment=False)
    family_members = patient.patient_family_member_info.filter(is_visible=True)
    for member in family_members:
        member_uhid = member.uhid_number
        family_appointment = Appointment.objects.filter(
            Q(appointment_date__gte=datetime.now().date()) & Q(status=1) & ((Q(uhid__isnull=False) & Q(uhid=member_uhid)) | Q(family_member_id=member.id))).exclude(
            Q(appointment_mode="VC") & (Q(vc_appointment_status="4") | Q(payment_status__isnull=True))).filter(corporate_appointment=False)
        patient_appointment = patient_appointment.union(family_appointment)
    return patient_appointment.order_by('appointment_date', 'appointment_slot')


def get_report_info(hospital_code=None,specific_date=None):
    param = dict()
    param['hospital_code'] = hospital_code
    yesterday = datetime.today() - timedelta(days=1)
    if specific_date:
        try:
            yesterday = datetime.strptime(specific_date,"%d-%m-%Y")
        except Exception as error:
            logger.info("Error while parsing date : %s"%(str(error)))
    unique_uhid_info = set(Patient.objects.filter(
                    uhid_number__isnull=False, mobile_verified=True, created_at__date=yesterday.date()).values_list('uhid_number', flat=True))
    unique_uhid_info.update(set(FamilyMember.objects.filter(
                    uhid_number__isnull=False, is_visible=True, created_at__date=yesterday.date()).values_list('uhid_number', flat=True)))

    param['trans_date'] = yesterday.strftime("%Y-%m-%d")
    param['trans_time'] = yesterday.strftime("%I:%M %p")
    param['linked_user_count'] = len(unique_uhid_info)
    param['family_member_count'] = FamilyMember.objects.filter(is_visible=True, created_at__date=yesterday.date()).count()
    param['primary_user_count'] = Patient.objects.filter(mobile_verified=True, created_at__date=yesterday.date()).count() 
    param['android_download'] = MobileDevice.objects.filter(platform='Android', participant__created_at__date=yesterday.date()).count()
    param['ios_download'] = MobileDevice.objects.filter(platform='iOS', participant__created_at__date=yesterday.date()).count()
    param['hv_count'] = Appointment.objects.filter(created_at__date=yesterday.date(),booked_via_app=True, status=1, appointment_mode="HV", hospital__code=hospital_code).count() 
    param['vc_count'] = Appointment.objects.filter(created_at__date=yesterday.date(),booked_via_app=True, status=1, appointment_mode="VC", payment_status="success", hospital__code=hospital_code).count() 
    param['hc_count'] = HealthPackageAppointment.objects.filter(created_at__date=yesterday.date(), payment_id__status="success", appointment_status="Booked", hospital__code=hospital_code).count() 
    param['hv_amount'] = Payment.objects.filter(created_at__date=yesterday.date(), status="success", appointment__isnull=False, appointment__appointment_mode="HV", location__code=hospital_code).aggregate(amount=Sum('amount'))['amount']
    param['vc_amount'] = Payment.objects.filter(created_at__date=yesterday.date(), status="success", appointment__isnull=False, appointment__appointment_mode="VC", location__code=hospital_code).aggregate(amount=Sum('amount'))['amount']
    param['ip_deposit_amount'] = Payment.objects.filter(created_at__date=yesterday.date(),  payment_for_ip_deposit=True, status="success", location__code=hospital_code).aggregate(amount=Sum('amount'))['amount'] 
    param['hc_package_amount'] = Payment.objects.filter(created_at__date=yesterday.date(), payment_for_health_package=True, status="success", location__code=hospital_code).aggregate(amount=Sum('amount'))['amount'] 
    param['op_outstanding_amount'] = Payment.objects.filter(created_at__date=yesterday.date(), payment_for_op_billing=True, status="success", location__code=hospital_code).aggregate(amount=Sum('amount'))['amount'] 
    param['registration_amount'] = Payment.objects.filter(created_at__date=yesterday.date(), payment_for_health_package=True, status="success", location__code=hospital_code).aggregate(amount=Sum('amount'))['amount'] 
    param['registered_patient_count'] = Payment.objects.filter(created_at__date=yesterday.date(), payment_for_health_package=True, status="success", location__code=hospital_code).count() 
    param['home_collection_count'] = HomeCollectionAppointment.objects.filter(created_at__date=yesterday.date(), hospital__code=hospital_code).count() 
    param['home_service_count'] = PatientServiceAppointment.objects.filter(created_at__date=yesterday.date(), hospital__code=hospital_code).count() 
    param['preferred_hospital_count'] =  Patient.objects.filter(mobile_verified=True, created_at__date=yesterday.date(), favorite_hospital__code=hospital_code).count() 
    param['ip_deposit_count'] = Payment.objects.filter(created_at__date=yesterday.date(), payment_for_ip_deposit=True, status="success", location__code=hospital_code).count()
    
    return param


def assign_users(request_data,user_id):
    selected_patient = Patient.objects.filter(id=user_id).first()
    if not selected_patient:
        raise ValidationError("Invalid patient selected.")
    request_data["patient"] = selected_patient

    if request_data.get("family_member"):
        selected_patient = FamilyMember.objects.filter(id=request_data.get("family_member")).first()
        if not selected_patient:
            raise ValidationError("Invalid family member selected.")
        request_data["family_member"] = selected_patient

    if not selected_patient.uhid_number and not selected_patient.pre_registration_number:
        raise UserNotRegisteredException

    aadhar_number = request_data.pop("aadhar_number")
    dob = request_data.pop("dob")
    if request_data.get("family_member"):
        request_data["family_member"].aadhar_number = aadhar_number
        request_data["family_member"].dob = dob
        request_data["family_member"].save()
    else:
        request_data["patient"].aadhar_number = aadhar_number
        request_data["patient"].dob = dob
        request_data["patient"].save()

    return request_data


    
    