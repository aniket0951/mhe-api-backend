import json
from os import stat

from rest_framework.test import APIClient
from rest_framework.serializers import ValidationError

from apps.master_data.models import Hospital
from apps.appointments.models import Appointment
from apps.master_data.exceptions import HospitalDoesNotExistsValidationException
from utils.razorpay_util import RazorPayUtil

from .constants import PaymentConstants

client = APIClient()

class PaymentUtils:

    @staticmethod
    def create_razorpay_order_id(hospital_secret,amount,description,currency):
        razor_pay = RazorPayUtil(key_id=hospital_secret) if hospital_secret else RazorPayUtil()
        razor_pay.create_order(amount=amount,description=description,currency=currency)
        return razor_pay.order_id

    @staticmethod
    def get_hospital_from_location_code(location_code):
        hospital = None
        try:
            hospital = Hospital.objects.filter(code=location_code).first()
        except Exception:
            raise HospitalDoesNotExistsValidationException
        return hospital
    
    @staticmethod
    def get_appointment_instance(appointment):
        if not appointment:
            raise ValidationError("Please provide appointment id!")
        appointment_instance = Appointment.objects.filter(appointment_identifier=appointment).first()
        if not appointment_instance:
            raise ValidationError("Appointment is not available")
        return appointment_instance

    @staticmethod
    def set_param_for_appointment(param,appointment):
        if "token" not in param:
            param["token"] = {}
        param["token"]["appointment_id"] = appointment
        param["token"]["package_code"] = PaymentConstants.APPOINTMENT_PACKAGE_CODE
        param["token"]["transaction_type"] = PaymentConstants.APPOINTMENT_TRANSACTION_TYPE
        return param

    @staticmethod
    def set_payment_data_for_appointment(request,param,appointment_instance,hospital):
        payment_data = {}
        payment_data["processing_id"] = param["token"]["processing_id"]
        payment_data["appointment"] = appointment_instance.id
        payment_data["patient"] = request.user.id
        payment_data["payment_done_for_patient"] = appointment_instance.patient.id
        payment_data["location"] = hospital.id
        if appointment_instance.family_member:
            payment_data["payment_done_for_patient"] = None
            payment_data["payment_done_for_family_member"] = appointment_instance.family_member.id
        return payment_data

    @staticmethod
    def add_items_tariff_price(calculated_amount,location_code):
        response = client.post(
                            PaymentConstants.URL_ITEM_TERIFF_PRICE,
                            json.dumps({
                                'item_code': PaymentConstants.TERRIF_PRICE_ITEM_CODE,
                                'location_code': location_code
                            }), 
                            content_type= PaymentConstants.JSON_CONTENT_TYPE
                        )

        if response.status_code == 200 and response.data["success"] == True:
            calculated_amount += int(float(response.data["data"][0]["ItemPrice"]))
        return calculated_amount

    @staticmethod
    def get_consultation_charges(location_code,appointment_instance,uhid,order_date):
        response_doctor_charges = client.post(
                                        PaymentConstants.URL_CONSULTATION_CHARGES,
                                        json.dumps({
                                            'location_code': location_code, 
                                            'specialty_code': appointment_instance.department.code, 
                                            'doctor_code': appointment_instance.doctor.code, 
                                            "uhid":uhid, 
                                            'order_date': order_date
                                        }), 
                                        content_type=PaymentConstants.JSON_CONTENT_TYPE
                                    )
        return response_doctor_charges

    @staticmethod
    def validate_order_amount_for_appointments(request,appointment_instance,location_code,param):
        calculated_amount = 0

        uhid = appointment_instance.uhid
        order_date = appointment_instance.appointment_date.strftime("%d%m%Y")

        if request.data.get("registration_payment", False):
            uhid = "None"
            calculated_amount = PaymentUtils.add_items_tariff_price(calculated_amount,location_code)
        
        response_doctor_charges = PaymentUtils.get_consultation_charges(location_code,appointment_instance,uhid,order_date)
        calculated_amount = PaymentUtils.calculate_amount_based_on_appointment_mode(calculated_amount,response_doctor_charges,appointment_instance)

        if not (calculated_amount == int(float(param["token"]["accounts"][0]["amount"]))):
            raise ValidationError(PaymentConstants.ERROR_MESSAGE_PRICE_UPDATED)


    @staticmethod
    def calculate_amount_based_on_appointment_mode(calculated_amount,response_doctor_charges,appointment_instance):
        if  response_doctor_charges.status_code == 200 and \
            response_doctor_charges.data and \
            response_doctor_charges.data.get("success") and \
            response_doctor_charges.data.get("success") == True:

            response_doctor_charges_data = response_doctor_charges.data.get("data")
            if response_doctor_charges_data:

                if appointment_instance.appointment_mode == PaymentConstants.APPOINTMENT_MODE_HV:
                    calculated_amount = calculated_amount + \
                        int(float(response_doctor_charges_data.get(PaymentConstants.MANIPAL_OPD_CONS_CHARGES)))

                if appointment_instance.appointment_mode == PaymentConstants.APPOINTMENT_MODE_VC:
                    calculated_amount = calculated_amount + \
                        int(float(response_doctor_charges_data.get(PaymentConstants.MANIPAL_VC_CONS_CHARGES)))

                if appointment_instance.appointment_mode == PaymentConstants.APPOINTMENT_MODE_PR:
                    calculated_amount = calculated_amount + \
                        int(float(response_doctor_charges_data.get(PaymentConstants.MANIPAL_PR_CONS_CHARGES)))

        return calculated_amount

    @staticmethod
    def set_order_id_for_appointments(param,payment_data):
        hospital_secret = param["token"]["auth"]["key"]
        amount = int(float(param["token"]["accounts"][0]["amount"]))
        description = PaymentConstants.RAZORPAY_APPOINTMENT_PAYMENT_DESCRIPTION
        currency = PaymentConstants.RAZORPAY_PAYMENT_CURRENCY
        order_id = PaymentUtils.create_razorpay_order_id(
                                    hospital_secret=hospital_secret,
                                    amount=amount,
                                    description=description,
                                    currency=currency
                                )
        param["token"]["order_id"] = order_id
        payment_data["razor_order_id"] = order_id
        return param,payment_data







    @staticmethod
    def get_health_package_code(request):
        package_code = request.data.get("package_code")
        package_code_list = package_code.split(",")
        package_code = "||".join(package_code_list)
        return package_code,package_code_list

    @staticmethod
    def set_param_for_health_package(param,package_code,appointment):
        if "token" not in param:
            param["token"] = {}
        param["token"]["package_code"] = package_code
        param["token"]["appointment_id"] = appointment
        param["token"]["transaction_type"] = PaymentConstants.HEALTH_PACKAGE_TRANSACTION_TYPE
        return param

    @staticmethod
    def set_payment_data_for_health_package(request,param,hospital,appointment_instance,registration_payment,family_member):
        payment_data = {}
        payment_data["processing_id"] = param.get("token").get("processing_id")
        payment_data["patient"] = request.user.id
        payment_data["location"] = hospital.id
        payment_data["health_package_appointment"] = appointment_instance.id
        payment_data["payment_for_health_package"] = True
        if registration_payment:
            payment_data["payment_for_uhid_creation"] = True
        if family_member is not None:
            payment_data["payment_done_for_family_member"] = family_member
        else:
            payment_data["payment_done_for_patient"] = request.user.id
        return payment_data

    @staticmethod
    def validate_order_amount_for_health_package(param,location_code,package_code_list):
        calculated_amount = 0
        for package in package_code_list:
            response = client.post(
                                PaymentConstants.URL_HEALTH_PACKAGE_PRICE,
                                json.dumps({
                                    'location_code': location_code,
                                    'package_code': package
                                }), 
                                content_type=PaymentConstants.JSON_CONTENT_TYPE
                            )
            if response.status_code == 200 and response.data["success"] == True:
                calculated_amount += int(float(response.data["message"]))
        if not (calculated_amount == int(float(param["token"]["accounts"][0]["amount"]))):
            raise ValidationError(PaymentConstants.ERROR_MESSAGE_PRICE_UPDATED)

    @staticmethod
    def set_order_id_for_health_package(param,payment_data):
        hospital_secret = param["token"]["auth"]["key"]
        amount = int(float(param["token"]["accounts"][0]["amount"]))
        description = PaymentConstants.RAZORPAY_HEALTH_PACKAGE_PURCHASE_DESCRIPTION
        currency = PaymentConstants.RAZORPAY_PAYMENT_CURRENCY
        order_id = PaymentUtils.create_razorpay_order_id(
                                    hospital_secret=hospital_secret,
                                    amount=amount,
                                    description=description,
                                    currency=currency
                                )
        param["token"]["order_id"] = order_id
        payment_data["razor_order_id"] = order_id
        return param,payment_data








    @staticmethod
    def set_param_for_uhid(param,location_code):
        if "token" not in param:
            param["token"] = {}
        param["token"]["transaction_type"] = PaymentConstants.UHID_TRANSACTION_TYPE
        param["token"]["payment_location"] = location_code
        return param

    @staticmethod
    def set_payment_data_for_uhid(request,param,hospital,family_member):
        payment_data = {}
        payment_data["processing_id"] = param["token"]["processing_id"]
        payment_data["patient"] = request.user.id
        payment_data["location"] = hospital.id
        if family_member is not None:
            payment_data["payment_done_for_family_member"] = family_member
        else:
            payment_data["payment_done_for_patient"] = request.user.id
        return payment_data

    @staticmethod
    def validate_order_amount_for_uhid(param,location_code):
        calculated_amount = 0
        response = client.post(
                        PaymentConstants.URL_ITEM_TERIFF_PRICE,
                        json.dumps({
                            'item_code': PaymentConstants.TERRIF_PRICE_ITEM_CODE,
                            'location_code': location_code
                        }), 
                        content_type=PaymentConstants.JSON_CONTENT_TYPE
        )

        if response.status_code == 200 and response.data["success"] == True:
            calculated_amount += int(float(response.data["data"][0]["ItemPrice"]))

        if not (calculated_amount == int(float(param["token"]["accounts"][0]["amount"]))):
            raise ValidationError(PaymentConstants.ERROR_MESSAGE_PRICE_UPDATED)

    @staticmethod
    def set_order_id_for_uhid(param,payment_data):
        hospital_secret = param["token"]["auth"]["key"]
        amount = int(float(param["token"]["accounts"][0]["amount"]))
        description = PaymentConstants.RAZORPAY_UHID_PURCHASE_DESCRIPTION
        currency = PaymentConstants.RAZORPAY_PAYMENT_CURRENCY
        order_id = PaymentUtils.create_razorpay_order_id(
                                    hospital_secret=hospital_secret,
                                    amount=amount,
                                    description=description,
                                    currency=currency
                                )
        param["token"]["order_id"] = order_id
        payment_data["razor_order_id"] = order_id
        return param,payment_data




    


    

    @staticmethod
    def set_param_for_op_bill(param,location_code,episode_no):
        if "token" not in param:
            param["token"] = {}
        param["token"]["transaction_type"] = PaymentUtils.OP_BILL_TRANSACTION_TYPE
        param["token"]["appointment_id"] = episode_no
        param["token"]["payment_location"] = location_code
        return param

    @staticmethod
    def set_payment_data_for_op_bill(request,param,hospital,family_member,episode_no):
        payment_data = {}
        payment_data["processing_id"] = param["token"]["processing_id"]
        payment_data["patient"] = request.user.id
        payment_data["location"] = hospital.id
        if family_member is not None:
            payment_data["payment_done_for_family_member"] = family_member
        else:
            payment_data["payment_done_for_patient"] = request.user.id
        payment_data["payment_for_op_billing"] = True
        payment_data["episode_number"] = episode_no
        return payment_data

    @staticmethod
    def validate_order_amount_for_op_bill(param,location_code,episode_no):
        calculated_amount = 0

        response = client.post(
                        PaymentConstants.URL_OP_BILL_DETAILS,
                        json.dumps({
                            "uhid": param["token"]["accounts"][0]["account_number"], 
                            'location_code': location_code
                        }), 
                        content_type=PaymentConstants.ERROR_MESSAGE_PRICE_UPDATED
                    )
        
        if  response.status_code == 200 and \
            response.data and \
            response.data.get("success") == True and \
            response.data.get("data"):

            episode_list = response.data.get("data")
            for episode in episode_list:
                if episode.get("EpisodeNo") == episode_no:
                    calculated_amount += int(float(episode["OutStandingAmt"]))

        if not (calculated_amount == int(float(param["token"]["accounts"][0]["amount"]))):
            raise ValidationError(PaymentConstants.ERROR_MESSAGE_PRICE_UPDATED)

    @staticmethod
    def set_order_id_for_op_bill(param,payment_data):
            hospital_secret = param["token"]["auth"]["key"]
            amount = int(float(param["token"]["accounts"][0]["amount"]))
            description = PaymentConstants.RAZORPAY_OP_BILL_PAYMENT_DESCRIPTION
            currency = PaymentConstants.RAZORPAY_PAYMENT_CURRENCY
            order_id = PaymentUtils.create_razorpay_order_id(
                                        hospital_secret=hospital_secret,
                                        amount=amount,
                                        description=description,
                                        currency=currency
                                    )
            param["token"]["order_id"] = order_id
            payment_data["razor_order_id"] = order_id
            return param,payment_data
    


    



    @staticmethod
    def set_param_for_ip_deposit(param,location_code):
        if "token" not in param:
            param["token"] = {}
        param["token"]["transaction_type"] = PaymentConstants.IP_DEPOSIT_TRANSACTION_TYPE
        param["token"]["payment_location"] = location_code
        return param

    @staticmethod
    def set_payment_data_for_ip_deposit(request,param,hospital,family_member):
        payment_data = {}
        payment_data["processing_id"] = param["token"]["processing_id"]
        payment_data["patient"] = request.user.id
        payment_data["location"] = hospital.id
        if family_member is not None:
            payment_data["payment_done_for_family_member"] = family_member
        else:
            payment_data["payment_done_for_patient"] = request.user.id
        payment_data["payment_for_ip_deposit"] = True
        return payment_data

    @staticmethod
    def set_order_id_for_ip_deposit(param,payment_data):
        hospital_secret = param["token"]["auth"]["key"]
        amount = int(float(param["token"]["accounts"][0]["amount"]))
        description = PaymentConstants.RAZORPAY_IP_DEPOSIT_PAYMENT_DESCRIPTION
        currency = PaymentConstants.RAZORPAY_PAYMENT_CURRENCY
        order_id = PaymentUtils.create_razorpay_order_id(
                                    hospital_secret=hospital_secret,
                                    amount=amount,
                                    description=description,
                                    currency=currency
                                )
        param["token"]["order_id"] = order_id
        payment_data["razor_order_id"] = order_id
        return param,payment_data