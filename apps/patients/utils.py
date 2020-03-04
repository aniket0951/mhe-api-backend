from rest_framework.serializers import ValidationError
from rest_framework.test import APIRequestFactory

from apps.master_data.views import ValidateOTPView


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

    if not (response.status_code == 200 and response.data['success']):
        raise ValidationError(response.data['message'])

    sorted_keys = ['age', 'DOB', 'email', 'HospNo',
                   'mobile', 'first_name', 'gender', 'Status']
    uhid_user_info = {}
    for index, key in enumerate(sorted(response.data['data'].keys())):
        if key in ['Age', 'DOB', 'HospNo', 'Status']:
            continue
        if not response.data['data'][key]:
            uhid_user_info[key] = None
        if key == 'MobileNo' and len(response.data['data'][key]) == 10:
            response.data['data'][key] = '+91' + response.data['data'][key]

        uhid_user_info[sorted_keys[index]] = response.data['data'][key]

    uhid_user_info['uhid_number'] = uhid_number
    uhid_user_info['raw_info_from_manipal_API'] = response.data['data']
    return uhid_user_info
