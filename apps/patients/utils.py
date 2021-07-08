
from django.contrib.auth import authenticate
from apps.patients.exceptions import InvalidCredentialsException
from django.conf import settings
from django.utils.crypto import get_random_string
from apps.patients.serializers import FamilyMemberCorporateHistorySerializer
from apps.patients.models import FamilyMember, FamilyMemberCorporateHistory, OtpGenerationCount, Patient
from apps.master_data.models import Hospital
from apps.master_data.views import LinkUhidView, ValidateOTPView
from rest_framework.serializers import ValidationError
from rest_framework.test import APIRequestFactory
from axes.models import AccessAttempt
from datetime import datetime, timedelta
from .constants import PatientsConstants

def check_max_otp_retries(user_obj):
    check_max_otp_retries_from_mobile_number(user_obj.mobile)

def check_max_otp_retries_from_mobile_number(mobile_number):
    otp_instance = OtpGenerationCount.objects.filter(mobile=mobile_number).first()
    if not otp_instance:
        otp_instance = OtpGenerationCount.objects.create(mobile=mobile_number, otp_generation_count=1)

    current_time = datetime.today()
    delta = current_time - otp_instance.updated_at
    if delta.seconds <= 600 and otp_instance.otp_generation_count >= 5:
        raise ValidationError(PatientsConstants.OTP_MAX_LIMIT)

    if delta.seconds > 600:
        otp_instance.otp_generation_count = 1
        otp_instance.save()

    if delta.seconds <= 600:
        otp_instance.otp_generation_count += 1
        otp_instance.save()

def fetch_uhid_user_details(request):
    uhid_number = request.data.get('uhid_number')
    otp = request.data.get('otp')
    if not (uhid_number and otp):
        raise ValidationError('UHID or OTP is missing!')

    otp = str(otp)
    factory = APIRequestFactory()
    proxy_request = factory.post('', {"uhid": uhid_number, "otp": otp}, format='json')
    response = ValidateOTPView().as_view()(proxy_request)
    if not (response.status_code == 200 and response.data['success']):
        raise ValidationError(response.data['message'])

    sorted_keys = ['age', 'DOB', 'email', 'HospNo',
                   'mobile', 'first_name', 'gender', 'Status']
    uhid_user_info = {}
    for index, key in enumerate(sorted(response.data['data'].keys())):
        if key in ['Age', 'DOB', 'HospNo', 'Status']:
            continue
        if not response.data['data'][key]:
            response.data['data'][key] = None
        if key == 'MobileNo' and len(response.data['data'][key]) == 10:
            response.data['data'][key] = '+91' + response.data['data'][key]

        if key == 'MobileNo' and len(response.data['data'][key]) == 12:
            response.data['data'][key] = '+' + response.data['data'][key]

        uhid_user_info[sorted_keys[index]] = response.data['data'][key]
    uhid_user_info['uhid_number'] = uhid_number
    uhid_user_info['raw_info_from_manipal_API'] = response.data['data']

    return uhid_user_info


def link_uhid(request):
    uhid = request.data.get('uhid_number')
    link_uhid_from_uhid_number(uhid)

def link_uhid_from_uhid_number(uhid):
    if not uhid:
        return False
    factory = APIRequestFactory()
    proxy_request = factory.post('', {"uhid": uhid}, format='json')
    response = LinkUhidView().as_view()(proxy_request)
    if not (response.status_code == 200 and response.data['success']):
        return False
    return True

def covid_registration_mandatory_check(request_data):
    mandatory_check = [ field for field in ("dose_type",'dob','preferred_hospital','aadhar_number') if not request_data.get(field) or not str(request_data.get(field)).strip() ]
    if mandatory_check:
        raise ValidationError("%s is mandatory"%(str(mandatory_check[0])))

def assign_hospital(request_data):
    hospital_instance = Hospital.objects.filter(id=request_data.get("preferred_hospital")).first()
    if not hospital_instance:
        raise ValidationError("Invalid hospital provided.")
    request_data["preferred_hospital"] = hospital_instance
    return request_data

def validate_uhid_family_members(member,patient,family_member,uhid_number):
    if not member:
        raise ValidationError("Family Member not Available")

    if patient.uhid_number == uhid_number:
        raise ValidationError(PatientsConstants.CANT_ASSOCIATE_UHID_TO_FAMILY_MEMBER)

    if family_member.filter(uhid_number=uhid_number).exists():
        raise ValidationError(PatientsConstants.UHID_LINKED_TO_FAMILY_MEMBER)

def validate_uhid_patients(patient,uhid_number):
    if patient.uhid_number == uhid_number:
        raise ValidationError("This UHID is already linked to your account!")
        
    if Patient.objects.filter(uhid_number=uhid_number).exists():
        raise ValidationError("There is an existing user with different contact number on our platform with this UHID. Please contact our customer care for more information.")
    
    if FamilyMember.objects.filter(patient_info=patient,uhid_number=uhid_number,is_visible=True).exists():
        raise ValidationError(PatientsConstants.UHID_LINKED_TO_FAMILY_MEMBER)

def make_family_member_corporate(serializer,family_member_object):
    if 'is_corporate' in serializer.validated_data and \
        serializer.validated_data['is_corporate'] and \
        family_member_object.patient_info and \
        family_member_object.patient_info.company_info:

        mapping_id = FamilyMemberCorporateHistory.objects.filter(family_member = family_member_object.id, company_info = family_member_object.patient_info.company_info.id)

        if not mapping_id:
            data = {
                "family_member" : family_member_object.id,
                "company_info"  : family_member_object.patient_info.company_info.id
            }
            FamilyMemberCorporateHistorySerializer(data=data)
            FamilyMemberCorporateHistorySerializer.save()

def process_is_email_to_be_verified(serializer,family_member_object,request_patient):
    is_email_to_be_verified=False
    
    if 'email' in serializer.validated_data and not family_member_object.email == serializer.validated_data['email']:
        is_email_to_be_verified=True
        if serializer.validated_data['email'] == request_patient.email and request_patient.email_verified:
            is_email_to_be_verified=False
        family_member_object=serializer.save(email_verified=not is_email_to_be_verified)
    else:
        family_member_object=serializer.save()

    if is_email_to_be_verified:
        random_email_otp=get_random_string(length=settings.OTP_LENGTH, allowed_chars='0123456789')
        otp_expiration_time=datetime.now() + timedelta(seconds=int(settings.OTP_EXPIRATION_TIME))

        family_member_object.email_verified=False
        family_member_object.email_verification_otp=random_email_otp
        family_member_object.email_otp_expiration_time=otp_expiration_time
        family_member_object.save()
    return family_member_object

def save_authentication_type(authenticated_patient,email,facebook_id,google_id,apple_id,apple_email):
    if authenticated_patient.mobile_verified:
        if email:
            authenticated_patient.email = email
        if facebook_id:
            authenticated_patient.facebook_id = facebook_id
        if google_id:
            authenticated_patient.google_id = google_id
        if apple_id:
            authenticated_patient.apple_id = apple_id
            authenticated_patient.apple_email = apple_email
        authenticated_patient.save()

def validate_access_attempts(username,password,request):
    if not (username and password):
        raise InvalidCredentialsException

    authenticated_patient = authenticate(request=request, username=username,password=password)

    access_log = AccessAttempt.objects.filter(username=username).first()
    if not authenticated_patient:
        if access_log:
            attempt = access_log.failures_since_start
            if attempt < 3:
                message = settings.WRONG_OTP_ATTEMPT_ERROR.format(attempt)
                raise ValidationError(message)
            if attempt >= 3:
                message = settings.MAX_WRONG_OTP_ATTEMPT_ERROR
                raise ValidationError(message)
        raise InvalidCredentialsException

    if access_log:
        access_log.delete()
    
    return authenticated_patient