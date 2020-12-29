import json
from os import stat
from datetime import date, datetime, timedelta

from django.db import models
from django.conf import settings

from rest_framework.test import APIClient
from rest_framework.serializers import ValidationError

from apps.master_data.models import Hospital
from apps.master_data.exceptions import HospitalDoesNotExistsValidationException
from apps.appointments.models import Appointment,HealthPackageAppointment
from apps.appointments.serializers import AppointmentSerializer,HealthPackageAppointmentSerializer
from apps.appointments.views import AppointmentPaymentView
from apps.appointments.utils import cancel_and_refund_parameters
from apps.payments.models import Payment
from apps.payments.exceptions import (
                        ProcessingIdDoesNotExistsValidationException,
                        MandatoryOrderIdException,
                        MandatoryProcessingIdException
                    )
from apps.patients.models import FamilyMember, Patient
from apps.patients.serializers import (FamilyMemberSpecificSerializer,
                                       PatientSpecificSerializer)

from utils.razorpay_util import RazorPayUtil
from utils.razorpay_payment_parameter_generator import get_hospital_key_info

from .constants import PaymentConstants
from .serializers import PaymentSerializer

client = APIClient()

class PaymentUtils:

    @staticmethod
    def create_razorpay_order_id(hospital_secret,amount,description,currency):
        razor_pay = RazorPayUtil(key_id=hospital_secret) if hospital_secret else RazorPayUtil()
        razor_pay.create_order(amount=amount,description=description,currency=currency)
        return razor_pay.order_id

    @staticmethod
    def get_razorpay_order_details(hospital_secret,order_id):
        razor_pay = RazorPayUtil(key_id=hospital_secret,order_id=order_id)
        return razor_pay.fetch_order()



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
    def get_payment_instance(processing_id,razor_order_id):
        if not processing_id:
            raise MandatoryProcessingIdException
        if not razor_order_id:
            raise MandatoryOrderIdException
        payment_instance = None
        try:
            payment_instance = Payment.objects.get(
                                        processing_id=processing_id,
                                        razor_order_id=razor_order_id
                                    )
        except Exception:
            raise ProcessingIdDoesNotExistsValidationException
        return payment_instance

    @staticmethod
    def get_hospital_key_info_from_payment_instance(payment_instance):
        if not payment_instance or not payment_instance.location or not payment_instance.location.code:
            raise HospitalDoesNotExistsValidationException
        hospital_code = payment_instance.location.code
        hospital_key_info = get_hospital_key_info(hospital_code)
        return hospital_key_info

    @staticmethod
    def get_razorpay_order_details_payment_instance(payment_instance,razor_order_id):
        hospital_key_info = PaymentUtils.get_hospital_key_info_from_payment_instance(payment_instance)
        hospital_secret = settings.RAZOR_KEY_ID or hospital_key_info.secret_key
        return PaymentUtils.get_razorpay_order_details(hospital_secret,razor_order_id)




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
        payment_data["amount"] = amount
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
        payment_data["amount"] = amount
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
        payment_data["amount"] = amount
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
            payment_data["amount"] = amount
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
        payment_data["amount"] = amount
        return param,payment_data


    @staticmethod
    def initialize_payment_details(payment_response):
        payment = {}
        payment["uhid_number"] = payment_response.get("account_number").upper() if payment_response.get("account_number") else None
        return payment
    
    @staticmethod
    def get_new_appointment_id(payment_response):
        new_appointment_id = None
        payment_paydetail = payment_response.get("payDetailAPIResponse")
        if payment_paydetail and payment_paydetail.get("BillDetail"):
            bill_detail = json.loads(payment_paydetail["BillDetail"])[0]
            new_appointment_id = bill_detail["AppointmentId"]
        return new_appointment_id

    @staticmethod
    def set_payment_details_for_appointment_health_package(payment_instance,payment_response,payment):
        if payment_instance.appointment or payment_instance.payment_for_health_package:
            payment_paydetail = payment_response["payDetailAPIResponse"]
            if payment_paydetail["BillDetail"]:
                bill_detail = json.loads(
                    payment_paydetail["BillDetail"])[0]
                new_appointment_id = bill_detail["AppointmentId"]
                payment["receipt_number"] = bill_detail["ReceiptNo"]
        return payment

    @staticmethod
    def set_payment_details_for_uhid_with_appointment_health_package(payment_instance,payment_response,payment):
        if payment_instance.payment_for_uhid_creation:
            if payment_instance.appointment or payment_instance.payment_for_health_package:
                payment = PaymentUtils.set_payment_details_for_appointment_health_package(payment_instance,payment_response,payment)
            else:
                payment_paydetail = payment_response["payDetailAPIResponse"]
                payment["receipt_number"] = payment_paydetail["receiptNo"]
        return payment

    @staticmethod
    def set_payment_details_for_op_billing(payment_instance,payment_response,payment):
        if payment_instance.payment_for_op_billing:
            payment_paydetail = payment_response["opPatientBilling"]
            if payment_paydetail["BillDetail"]:
                bill_detail = json.loads(payment_paydetail["BillDetail"])[0]
                payment["receipt_number"] = bill_detail["BillNo"]
                payment["episode_number"] = bill_detail["EpisodeNo"]
        return payment

    @staticmethod
    def set_payment_details_for_ip_deposit(payment_instance,payment_response,payment):
        if payment_instance.payment_for_ip_deposit:
            payment_paydetail = payment_response["onlinePatientDeposit"]
            if payment_paydetail["RecieptNumber"]:
                bill_detail = json.loads(payment_paydetail["RecieptNumber"])[0]
                payment["receipt_number"] = bill_detail["ReceiptNo"]
        return payment

    @staticmethod
    def update_payment_details(payment_instance,payment_response,payment):
        payment["status"] = payment_response["status"]
        payment["payment_method"] = payment_response["card_type"] + \
            "-" + payment_response["mode"]
        payment["transaction_id"] = payment_response["txnid"]
        payment["amount"] = payment_response["net_amount_debit"]
        payment_serializer = PaymentSerializer(payment_instance, data=payment, partial=True)
        payment_serializer.is_valid(raise_exception=True)
        payment_serializer.save()
    
    @staticmethod
    def initialize_uhid_info(payment):
        uhid_info = {}
        if payment["uhid_number"] and (payment["uhid_number"][:2] == "MH" or payment["uhid_number"][:3] == "MMH"):
            uhid_info["uhid_number"] = payment["uhid_number"]
        return uhid_info

    @staticmethod
    def payment_for_uhid_creation_appointment(payment_instance):
        if payment_instance.appointment:
            appointment = Appointment.objects.filter(id=payment_instance.appointment.id).first()
            appointment.status = 6
            appointment.save()

    @staticmethod
    def payment_for_uhid_creation_payment_done_for_patient(payment_instance,uhid_info):
        if payment_instance.payment_done_for_patient:
            patient = Patient.objects.filter(id=payment_instance.payment_done_for_patient.id).first()
            patient_serializer = PatientSpecificSerializer(patient, data=uhid_info, partial=True)
            patient_serializer.is_valid(raise_exception=True)
            patient_serializer.save()

    @staticmethod
    def payment_for_uhid_creation_payment_done_for_family_member(payment_instance,uhid_info):
        if payment_instance.payment_done_for_family_member:
            family_member = FamilyMember.objects.filter(id=payment_instance.payment_done_for_family_member.id).first()
            patient_serializer = FamilyMemberSpecificSerializer(family_member, data=uhid_info, partial=True)
            patient_serializer.is_valid(raise_exception=True)
            patient_serializer.save()

    @staticmethod
    def payment_for_uhid_creation(payment_instance,uhid_info):
        if payment_instance and payment_instance.payment_for_uhid_creation:
            PaymentUtils.payment_for_uhid_creation_appointment(payment_instance)
            PaymentUtils.payment_for_uhid_creation_payment_done_for_patient(payment_instance,uhid_info)
            PaymentUtils.payment_for_uhid_creation_payment_done_for_family_member(payment_instance,uhid_info)
    
    @staticmethod
    def payment_for_scheduling_appointment(payment_instance,payment_response,payment):
        if payment_instance.appointment:
            appointment = Appointment.objects.filter(
                id=payment_instance.appointment.id).first()
            update_data = {"payment_status": payment_response["status"]}
            update_data["consultation_amount"] = payment_instance.amount
            if payment_instance.payment_for_uhid_creation:
                update_data["appointment_identifier"] = PaymentUtils.get_new_appointment_id(payment_response)
                update_data["status"] = 1
                update_data["uhid"] = payment["uhid_number"]
            appointment_serializer = AppointmentSerializer(
                appointment, data=update_data, partial=True)
            appointment_serializer.is_valid(raise_exception=True)
            appointment_serializer.save()

    @staticmethod
    def get_health_package_name(appointment_instance):
        package_name = ""
        package_list = appointment_instance.health_package.all()
        for package in package_list:
            if not package_name:
                package_name = package.name
            else:
                package_name = package_name + "," + package.name
        return package_name

    @staticmethod
    def payment_for_health_package(payment_instance,payment_response):
        if payment_instance.payment_for_health_package:
            appointment_instance = HealthPackageAppointment.objects.filter(id=payment_instance.health_package_appointment.id).first()
            update_data = {}
            update_data["payment"] = payment_instance.id
            package_name = PaymentUtils.get_health_package_name(appointment_instance)
            if payment_instance.payment_done_for_patient:
                patient = Patient.objects.filter(id=payment_instance.payment_done_for_patient.id).first()
            if payment_instance.payment_done_for_family_member:
                family_member = FamilyMember.objects.filter(id=payment_instance.payment_done_for_family_member.id).first()
            if payment_instance.payment_for_uhid_creation:
                update_data["appointment_identifier"] = PaymentUtils.get_new_appointment_id(payment_response)
            appointment_serializer = HealthPackageAppointmentSerializer(appointment_instance, data=update_data, partial=True)
            appointment_serializer.is_valid(raise_exception=True)
            appointment_serializer.save()


    @staticmethod
    def update_payment_details_with_manipal(payment_instance,razor_order_id):
        date_time = None
        if payment_instance.appointment and payment_instance.appointment.appointment_date and payment_instance.appointment.appointment_slot:
            datetime_object = datetime.combine(payment_instance.appointment.appointment_date,payment_instance.appointment.appointment_slot)
            date_time = datetime_object.strftime("%Y%m%d")

        appointment_type = ""
        if payment_instance.payment_for_health_package:
            appointment_type = "H"
        if payment_instance.appointment:
            appointment_type = "A"

        payment_update_request = {
            "uhid":payment_instance.patient.uhid_number if payment_instance and payment_instance.patient and payment_instance.patient.uhid_number else None,
            "transaction_number":razor_order_id,
            "processing_id":payment_instance.processing_id,
            "amt":str(payment_instance.amount),
            "location_code":payment_instance.location.code,
            "app_date":date_time,
            "type":appointment_type,
            "app_id":payment_instance.appointment.appointment_identifier if payment_instance and payment_instance.appointment and payment_instance.appointment.appointment_identifier else None
        }
        payment_update_response = AppointmentPaymentView.as_view()(cancel_and_refund_parameters(payment_update_request))
        return payment_update_response