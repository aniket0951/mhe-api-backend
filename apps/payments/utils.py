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
from apps.appointments.views import AppointmentPaymentView,UHIDPaymentView
from apps.appointments.utils import cancel_and_refund_parameters
from apps.payments.models import Payment
from apps.payments.exceptions import (
                        InvalidGeneratedUHIDException, ProcessingIdDoesNotExistsValidationException,
                        MandatoryOrderIdException,
                        MandatoryProcessingIdException,
                        UHIDRegistrationFailedException,
                        TransactionFailedException,
                        AppointmentCreationFailedException
                    )
from apps.patients.models import FamilyMember, Patient
from apps.patients.serializers import (FamilyMemberSpecificSerializer,
                                       PatientSpecificSerializer)

from utils.razorpay_util import RazorPayUtil
from utils.razorpay_payment_parameter_generator import get_hospital_key_info

from .constants import PaymentConstants
from .serializers import PaymentSerializer

client = APIClient()
AMOUNT_OFFSET = settings.RAZOR_AMOUNT_OFFSET

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
    def get_razorpay_fetch_order_payment_details(hospital_secret,order_id):
        razor_pay = RazorPayUtil(key_id=hospital_secret,order_id=order_id)
        return razor_pay.fetch_payments_of_order()

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
    def get_health_package_appointment(appointment):
        if not appointment:
            raise ValidationError("Please provide appointment id!")
        appointment_instance = HealthPackageAppointment.objects.filter(appointment_identifier=appointment).first()
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
    def get_razorpay_fetch_order_payments_payment_instance(order_details,payment_instance,razor_order_id):
        hospital_key_info = PaymentUtils.get_hospital_key_info_from_payment_instance(payment_instance)
        hospital_secret = settings.RAZOR_KEY_ID or hospital_key_info.secret_key
        order_payment_data = PaymentUtils.get_razorpay_fetch_order_payment_details(hospital_secret,razor_order_id)
        order_payment_data_item = dict()
        if order_payment_data.get("items") and len(order_payment_data.get("items"))>0:
            order_payment_data_item = order_payment_data.get("items")[-1]
            for item in order_payment_data.get("items"):
                if item.get("amount")==order_details.get("amount") and item.get("status")==PaymentConstants.RAZORPAY_PAYMENT_STATUS_CAPTURED:
                    order_payment_data_item = item
        return order_payment_data_item

    @staticmethod
    def get_payment_amount(order_details):
        if order_details.get("amount") and AMOUNT_OFFSET:
            return int(order_details.get("amount"))/int(AMOUNT_OFFSET)
        return order_details.get("amount")


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





    @staticmethod
    def get_bill_details(payment_response,bill_detail_label,api_type):
        payment_paydetail = payment_response[api_type]
        bill_detail = {}
        if payment_paydetail[bill_detail_label]:
            bill_detail = json.loads(payment_paydetail[bill_detail_label])[0]
        return bill_detail

    @staticmethod
    def set_receipt_number(payment_instance,bill_details,payment):
        if payment_instance.appointment or payment_instance.payment_for_health_package or payment_instance.payment_for_uhid_creation:
            payment["receipt_number"] = bill_details.get("ReceiptNo") or ""
        return payment

    @staticmethod
    def set_payment_details_for_op_billing(payment_instance,payment_response,payment):
        if payment_instance.payment_for_op_billing:
            bill_detail = PaymentUtils.get_bill_details(payment_response,"BillDetail","opPatientBilling")
            payment["receipt_number"] = bill_detail["BillNo"]
            payment["episode_number"] = bill_detail["EpisodeNo"]
        return payment

    @staticmethod
    def set_payment_details_for_ip_deposit(payment_instance,payment_response,payment):
        if payment_instance.payment_for_ip_deposit:
            bill_detail = PaymentUtils.get_bill_details(payment_response,"RecieptNumber","onlinePatientDeposit")
            payment["receipt_number"] = bill_detail["ReceiptNo"]
        return payment

    @staticmethod
    def get_payment_method_from_order_payment_details(order_payment_details):
        payment_method = ""
        if order_payment_details.get("bank"):
            payment_method = order_payment_details.get("bank")
        elif order_payment_details.get("wallet"):
            payment_method = order_payment_details.get("wallet")
        elif order_payment_details.get("vpa"):
            payment_method = order_payment_details.get("vpa")
        return payment_method

    @staticmethod
    def validate_uhid_number(uhid_number):
        if uhid_number and len(uhid_number)>2 and (uhid_number[:2] == "MH" or uhid_number[:3] == "MMH"):
            return True
        return False

    @staticmethod
    def update_payment_details(payment_instance,payment_response,order_details,order_payment_details):
        payment = {}
        payment = PaymentUtils.set_receipt_number(payment_instance,payment_response,payment)
        payment["razor_payment_id"] = order_payment_details.get("id")
        payment["razor_invoice_id"] = order_payment_details.get("invoice_id")
        payment["payment_method"] = PaymentUtils.get_payment_method_from_order_payment_details(order_payment_details)
        payment["transaction_id"] = order_payment_details.get("id")
        payment["amount"] = PaymentUtils.get_payment_amount(order_details)
        payment_serializer = PaymentSerializer(payment_instance, data=payment, partial=True)
        payment_serializer.is_valid(raise_exception=True)
        payment_serializer.save()




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
    def payment_for_uhid_creation(payment_instance,payment_response):
        uhid_info = {"uhid_number":payment_response.get("uhid_number")}
        if payment_instance and payment_instance.payment_for_uhid_creation:
            PaymentUtils.payment_for_uhid_creation_appointment(payment_instance)
            PaymentUtils.payment_for_uhid_creation_payment_done_for_patient(payment_instance,uhid_info)
            PaymentUtils.payment_for_uhid_creation_payment_done_for_family_member(payment_instance,uhid_info)
    



    @staticmethod
    def payment_for_scheduling_appointment(payment_instance,payment_response,order_details):
        if payment_instance.appointment:
            appointment = Appointment.objects.filter(id=payment_instance.appointment.id).first()
            update_data = {
                "payment_status": payment_instance.status,
                "consultation_amount":PaymentUtils.get_payment_amount(order_details),
                "appointment_identifier":payment_response.get("appointment_identifier"),
                "status":1,
                "uhid":payment_response.get("uhid_number")
            }
            appointment_serializer = AppointmentSerializer(appointment, data=update_data, partial=True)
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
            update_data = {
                "payment" : payment_instance.id,
                "appointment_identifier" : payment_response.get("appointment_identifier")
            }

            # package_name = PaymentUtils.get_health_package_name(appointment_instance)
            # if payment_instance.payment_done_for_patient:
            #     patient = Patient.objects.filter(id=payment_instance.payment_done_for_patient.id).first()
            # if payment_instance.payment_done_for_family_member:
            #     family_member = FamilyMember.objects.filter(id=payment_instance.payment_done_for_family_member.id).first()
            
            appointment_serializer = HealthPackageAppointmentSerializer(appointment_instance, data=update_data, partial=True)
            appointment_serializer.is_valid(raise_exception=True)
            appointment_serializer.save()
    
    @staticmethod
    def get_patients_mobile_number(payment_instance):
        mobile_no = ""
        if payment_instance.payment_done_for_patient:
            patient = Patient.objects.filter(id=payment_instance.payment_done_for_patient.id).first()
            mobile_no = str(patient.mobile) if patient else ""
        elif payment_instance.payment_done_for_family_member:
            family_member = FamilyMember.objects.filter(id=payment_instance.payment_done_for_family_member.id).first()
            mobile_no = str(family_member.mobile)
        return mobile_no

    @staticmethod
    def update_uhid_payment_details_with_manipal(payment_instance,order_details):
        payment_update_request = {
            "location_code":payment_instance.location.code,
            "temp_id":PaymentConstants.UHID_PAYMENT_FRC_ID,
            "transaction_number":order_details.get("id"),
            "amt":str(PaymentUtils.get_payment_amount(order_details)),
            "mobile":PaymentUtils.get_patients_mobile_number(payment_instance)
        }
        payment_update_response = UHIDPaymentView.as_view()(cancel_and_refund_parameters(payment_update_request))
        if  not payment_update_response.status_code==200 or \
            not payment_update_response.data or \
            not payment_update_response.data.get("data"):
            raise UHIDRegistrationFailedException
        payment_response = payment_update_response.data.get("data")
        PaymentUtils.validate_uhid_number(payment_response.get("uhid_number"))
        return payment_response

    @staticmethod
    def get_appointment_type(payment_instance):
        appointment_type = ""
        if payment_instance.payment_for_health_package:
            appointment_type = "H"
        elif payment_instance.appointment:
            appointment_type = "A"
        return appointment_type
    
    @staticmethod
    def get_payment_appointment_date(payment_instance):
        date_time = None
        if payment_instance.appointment and payment_instance.appointment.appointment_date and payment_instance.appointment.appointment_slot:
            datetime_object = datetime.combine(payment_instance.appointment.appointment_date,payment_instance.appointment.appointment_slot)
            date_time = datetime_object.strftime("%Y%m%d")
        if payment_instance.health_package_appointment and payment_instance.health_package_appointment.created_at:
            datetime_object = payment_instance.health_package_appointment.created_at
            date_time = datetime_object.strftime("%Y%m%d")
        return date_time

    @staticmethod
    def serialize_payment_response(bill_details_response):
        payment_response = dict()
        if not bill_details_response.get("HospitalNo"):
            raise UHIDRegistrationFailedException
        if not PaymentUtils.validate_uhid_number(bill_details_response.get("HospitalNo")):
            raise InvalidGeneratedUHIDException
        if not bill_details_response.get("ReceiptNo"):
            raise TransactionFailedException
        if not bill_details_response.get("AppointmentId"):
            raise AppointmentCreationFailedException
        payment_response.update({
            "uhid_number":bill_details_response.get("HospitalNo"),
            "ReceiptNo":bill_details_response.get("ReceiptNo"),
            "appointment_identifier":bill_details_response.get("AppointmentId"),
            "StatusMessage":bill_details_response.get("StatusMessage")
        })
        return payment_response
        
    @staticmethod
    def get_uhid_number(payment_instance):
        uhid_number = None
        if payment_instance.payment_done_for_patient:
            uhid_number = payment_instance.payment_done_for_patient.uhid_number
        elif payment_instance.payment_done_for_family_member:
            uhid_number = payment_instance.payment_done_for_family_member.uhid_number
        return uhid_number

    @staticmethod
    def get_appointment_id_from_payment_instance(payment_instance):
        appointment_id = None
        if payment_instance:
            if payment_instance.appointment and payment_instance.appointment.appointment_identifier:
                appointment_id = payment_instance.appointment.appointment_identifier
            elif payment_instance.health_package_appointment and payment_instance.health_package_appointment.appointment_identifier:
                appointment_id = payment_instance.health_package_appointment.appointment_identifier
        return appointment_id


    @staticmethod
    def update_payment_details_with_manipal(payment_instance,order_details):

        payment_update_request = {
            "uhid":PaymentUtils.get_uhid_number(payment_instance),
            "transaction_number":order_details.get("id"),
            "processing_id":payment_instance.processing_id,
            "amt":str(PaymentUtils.get_payment_amount(order_details)),
            "location_code":payment_instance.location.code,
            "app_date":PaymentUtils.get_payment_appointment_date(payment_instance),
            "type":PaymentUtils.get_appointment_type(payment_instance),
            "app_id":PaymentUtils.get_appointment_id_from_payment_instance(payment_instance)
        }

        payment_update_response = AppointmentPaymentView.as_view()(cancel_and_refund_parameters(payment_update_request))

        if  not payment_update_response.status_code==200 or \
            not payment_update_response.data or \
            not payment_update_response.data.get("data"):
            raise TransactionFailedException

        bill_details_response = PaymentUtils.get_bill_details(payment_update_response.data.get("data"),"BillDetail","payDetailAPIResponse")

        return PaymentUtils.serialize_payment_response(bill_details_response)

    @staticmethod
    def update_manipal_on_payment(payment_instance,order_details):
        if payment_instance.payment_for_uhid_creation and not payment_instance.appointment and not payment_instance.payment_for_health_package:
            return PaymentUtils.update_uhid_payment_details_with_manipal(payment_instance,order_details)
        else:
            return PaymentUtils.update_payment_details_with_manipal(payment_instance,order_details)