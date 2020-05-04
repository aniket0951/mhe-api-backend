from rest_framework.test import APIRequestFactory
from apps.health_packages.models import HealthPackage

def cancel_and_refund_parameters(param, factory=APIRequestFactory()):
    return factory.post(
        '', param, format='json')

def rebook_parameters(instance, factory=APIRequestFactory()):
    param = {}
    param["app_id"] = instance.appointment_identifier
    health_packages = instance.health_package.all()
    code = ""
    for package in health_packages:
        if not code:
            code = package.code
        else:
            code = code + "||" + package.code
    param["package_code"] = code
    param["total_amount"] = str(instance.payment.amount)
    param["type"] = "H"
    param["receipt_no"] = instance.payment.receipt_number
    param["trans_id"] = instance.payment.transaction_id
    param["location_code"] = instance.hospital.code
    return factory.post(
        '', param, format='json')