from apps.patients.models import OtpGenerationCount
from apps.master_data.models import Hospital
from apps.master_data.views import LinkUhidView, ValidateOTPView
from rest_framework.serializers import ValidationError
from rest_framework.test import APIRequestFactory
from datetime import datetime
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
    proxy_request = factory.post(
        '', {"uhid": uhid_number, "otp": otp}, format='json')
    response = ValidateOTPView().as_view()(proxy_request)
    print(response.data)
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
