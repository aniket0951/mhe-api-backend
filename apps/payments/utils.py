
import time
import json
import logging
from datetime import date, datetime

from django.conf import settings

from rest_framework.test import APIClient
from rest_framework.serializers import ValidationError

from apps.master_data.models import Hospital
from apps.master_data.exceptions import HospitalDoesNotExistsValidationException
from apps.appointments.models import Appointment,HealthPackageAppointment
from apps.appointments.serializers import AppointmentSerializer,HealthPackageAppointmentSerializer
from apps.appointments.utils import cancel_and_refund_parameters
from apps.payments.models import Payment, UnprocessedTransactions
from apps.payments.views import AppointmentPaymentView, DriveRegistrationPaymentStatusView,UHIDPaymentView,OPBillingPaymentView,IPDepositPaymentView,CheckAppointmentPaymentStatusView
from apps.payments.exceptions import (
                        InvalidGeneratedUHIDException, 
                        ProcessingIdDoesNotExistsValidationException,
                        MandatoryOrderIdException,
                        MandatoryProcessingIdException, ProcessingIdDoesNotExistsValidationException200,
                        UHIDRegistrationFailedException,
                        AppointmentCreationFailedException,
                        ReceiptGenerationFailedException,
                        InvalidResponseFromManipalServers,
                        PaymentRecordNotAvailable,
                        NoResponseFromRazorPayException,
                        UnsuccessfulPaymentException,
                        BillNoNotGeneratedAvailable,
                        PaymentProcessingFailedRefundProcessed,
                        PaymentProcessingFailedRefundProcessedException
                    )
from apps.patients.models import FamilyMember, Patient
from apps.patients.serializers import (FamilyMemberSpecificSerializer,PatientSpecificSerializer)
from apps.additional_features.serializers import DriveBookingSerializer
from apps.additional_features.models import DriveBilling, DriveBooking
from apps.doctors.serializers import DoctorChargesSerializer

from utils.razorpay_util import RazorPayUtil
from utils.razorpay_payment_parameter_generator import get_hospital_key_info
from utils.send_invite import send_appointment_invitation

from .constants import PaymentConstants
from .serializers import PaymentSerializer,PaymentRefundSerializer, UnprocessedTransactionsSerializer

client = APIClient()
AMOUNT_OFFSET = settings.RAZOR_AMOUNT_OFFSET
logger = logging.getLogger('django')

class PaymentUtils:

    @staticmethod
    def create_razorpay_order_id(hospital_key,hospital_secret,amount,description,currency):
        razor_pay = RazorPayUtil(key_id=hospital_key,key_secret=hospital_secret) if hospital_key and hospital_secret else RazorPayUtil()
        razor_pay.create_order(amount=amount,description=description,currency=currency)
        return razor_pay.order_id

    @staticmethod
    def get_razorpay_order_details(hospital_key,hospital_secret,order_id):
        razor_pay = RazorPayUtil(key_id=hospital_key,key_secret=hospital_secret,order_id=order_id)
        return razor_pay.fetch_order()

    @staticmethod
    def get_razorpay_fetch_order_payment_details(hospital_key,hospital_secret,order_id):
        razor_pay = RazorPayUtil(key_id=hospital_key,key_secret=hospital_secret,order_id=order_id)
        return razor_pay.fetch_payments_of_order()

    @staticmethod
    def initiate_refund(hospital_key,hospital_secret,payment_id,amount_to_be_refunded):
        razor_pay = RazorPayUtil(key_id=hospital_key,key_secret=hospital_secret,payment_id=payment_id)
        refund_data = razor_pay.initiate_refunt(amount_to_be_refunded=amount_to_be_refunded)
        return refund_data

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
    def get_drive_booking_instance(drive_booking):
        if not drive_booking:
            raise ValidationError("Please provide drive booking id!")
        try:
            return DriveBooking.objects.get(id=drive_booking)
        except Exception as e:
            logger.debug("Exception in PaymentUtils -> get_drive_booking_instance : %s"%(str(e)))
            raise ValidationError("Drive booking is not available")
        

    @staticmethod
    def get_health_package_appointment(appointment):
        if not appointment:
            raise ValidationError("Please provide appointment id!")
        appointment_instance = HealthPackageAppointment.objects.filter(appointment_identifier=appointment).first()
        if not appointment_instance:
            raise ValidationError("Appointment is not available")
        return appointment_instance

    @staticmethod
    def get_payment_instance_from_order_id(razor_order_id):
        if not razor_order_id:
            raise MandatoryOrderIdException
        payment_instance = None
        try:
            payment_instance = Payment.objects.get(
                                        razor_order_id=razor_order_id
                                    )
        except Exception:
            raise ProcessingIdDoesNotExistsValidationException
        return payment_instance

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
    def get_razorpay_payment_instance(razor_order_id):
        if not razor_order_id:
            raise MandatoryOrderIdException
        payment_instance = None
        try:
            payment_instance = Payment.objects.get(razor_order_id=razor_order_id)
        except Exception:
            raise ProcessingIdDoesNotExistsValidationException200
        return payment_instance

    @staticmethod
    def get_order_id_from_webhook_request(request_data):
        razor_order_id = ""
        if  request_data and \
            request_data.get("payload") and \
            request_data.get("payload").get("payment") and \
            request_data.get("payload").get("payment").get("entity") and \
            request_data.get("payload").get("payment").get("entity").get("order_id"):
            razor_order_id = request_data.get("payload").get("payment").get("entity").get("order_id")
        return razor_order_id

    @staticmethod
    def get_payment_details_from_webhook_request(request_data):
        razor_payment_details = {}
        if  request_data and \
            request_data.get("payload") and \
            request_data.get("payload").get("payment") and \
            request_data.get("payload").get("payment").get("entity") and \
            request_data.get("payload").get("payment").get("entity").get("id"):
            razor_payment_details = request_data.get("payload").get("payment").get("entity")
        return razor_payment_details
                
    @staticmethod
    def validate_request_get_payment_instance(request):
        payment_instance = None
        if request.data.get("order_id") and request.data.get("processing_id"):
            processing_id = request.data.get("processing_id")
            razor_order_id = request.data.get("order_id")
            payment_instance = PaymentUtils.get_payment_instance(processing_id,razor_order_id)
        elif request.data.get("order_id"):
            razor_order_id = request.data.get("order_id")
            payment_instance = PaymentUtils.get_payment_instance_from_order_id(razor_order_id)
        elif request.data.get("event") and request.data.get("event") in [PaymentConstants.RAZORPAY_ORDER_PAID_EVENT,PaymentConstants.RAZORPAY_ORDER_PAYMENT_FAILED_EVENT]:
            razor_order_id = PaymentUtils.get_order_id_from_webhook_request(request.data)
            payment_instance = PaymentUtils.get_razorpay_payment_instance(razor_order_id)
        if not payment_instance:
            raise PaymentRecordNotAvailable
        return payment_instance

    @staticmethod
    def validate_and_wait_for_mobile_request(request,is_requested_from_mobile):
        payment_instance = PaymentUtils.validate_request_get_payment_instance(request)
        if payment_instance.payment_for_drive and is_requested_from_mobile:
            counter = 0
            while payment_instance.status==PaymentConstants.MANIPAL_PAYMENT_STATUS_INITIATED:
                time.sleep(5)
                payment_instance = PaymentUtils.validate_request_get_payment_instance(request)
                counter+=1
                if counter==5:
                    break
        return payment_instance

    @staticmethod
    def get_hospital_key_info_from_payment_instance(payment_instance):
        if not payment_instance or not payment_instance.location or not payment_instance.location.code:
            raise HospitalDoesNotExistsValidationException
        hospital_code = payment_instance.location.code
        hospital_key_info = get_hospital_key_info(hospital_code)
        return hospital_key_info

    @staticmethod
    def get_razorpay_order_details_payment_instance(payment_instance):
        razor_order_id = payment_instance.razor_order_id
        hospital_key_info = PaymentUtils.get_hospital_key_info_from_payment_instance(payment_instance)
        hospital_key = hospital_key_info.secret_key
        hospital_secret = hospital_key_info.secret_secret
        return PaymentUtils.get_razorpay_order_details(hospital_key,hospital_secret,razor_order_id)

    @staticmethod
    def get_razorpay_payment_data_from_order_id(hospital_key,hospital_secret,razor_order_id,order_details=None):
        if not order_details:
            order_details = PaymentUtils.get_razorpay_order_details(hospital_key,hospital_secret,razor_order_id)
        order_payment_data = PaymentUtils.get_razorpay_fetch_order_payment_details(hospital_key,hospital_secret,razor_order_id)
        order_payment_data_item = dict()
        if order_payment_data.get("items") and len(order_payment_data.get("items"))>0:
            for item in order_payment_data.get("items"):        
                if float(item.get("amount"))==float(order_details.get("amount")) and item.get("status") in [PaymentConstants.RAZORPAY_PAYMENT_STATUS_CAPTURED,PaymentConstants.RAZORPAY_PAYMENT_STATUS_REFUNDED]:
                    order_payment_data_item = item
        return order_payment_data_item

    @staticmethod
    def get_razorpay_fetch_order_payments_payment_instance(order_details,payment_instance):
        razor_order_id = payment_instance.razor_order_id
        hospital_key_info = PaymentUtils.get_hospital_key_info_from_payment_instance(payment_instance)
        hospital_key = hospital_key_info.secret_key
        hospital_secret = hospital_key_info.secret_secret
        order_payment_data_item = PaymentUtils.get_razorpay_payment_data_from_order_id(hospital_key,hospital_secret,razor_order_id,order_details)
        payment_instance.raw_info_from_salucro_response = order_payment_data_item or order_details 
        payment_instance.save()
        return order_payment_data_item

    @staticmethod
    def get_razorpay_order_payment_response(request,order_details,payment_instance):
        if request.data.get("event") and request.data.get("event") in [PaymentConstants.RAZORPAY_ORDER_PAID_EVENT,PaymentConstants.RAZORPAY_ORDER_PAYMENT_FAILED_EVENT]:
            order_payment_details = PaymentUtils.get_payment_details_from_webhook_request(request.data)
        else:
            order_payment_details = PaymentUtils.get_razorpay_fetch_order_payments_payment_instance(order_details,payment_instance)
        return order_payment_details

    @staticmethod
    def validate_order_details_status(order_details,order_payment_details,payment_instance):
        
        if not order_details.get("status"):
            raise NoResponseFromRazorPayException
    
        if order_details.get("status")==PaymentConstants.RAZORPAY_PAYMENT_STATUS_CREATED:
            raise UnsuccessfulPaymentException
        
        payment_instance.payment_method = PaymentUtils.get_payment_method_from_order_payment_details(order_payment_details)
        payment_instance.uhid_number = PaymentUtils.get_uhid_number(payment_instance)
        payment_instance.amount = PaymentUtils.get_payment_amount(order_details)
        payment_instance.transaction_id = order_payment_details.get("id")
        payment_instance.save()

        if  order_payment_details.get("status") and \
            order_payment_details.get("status")==PaymentConstants.RAZORPAY_PAYMENT_STATUS_FAILED:
            payment_instance.status = PaymentConstants.MANIPAL_PAYMENT_STATUS_FAILED
            payment_instance.save()
        
    
    @staticmethod
    def update_refund_payment_response(refunded_payment_details,payment_instance,amount):
        refund_param = dict()
        refund_param["status"] = PaymentConstants.MANIPAL_PAYMENT_STATUS_SUCCESS if refunded_payment_details.get("status") == PaymentConstants.RAZORPAY_PAYMENT_STATUS_PROCESSED else PaymentConstants.MANIPAL_PAYMENT_STATUS_FAILED
        refund_param["payment"] = payment_instance.id
        refund_param["uhid_number"] = payment_instance.uhid_number
        refund_param["processing_id"] = payment_instance.processing_id
        refund_param["transaction_id"] = payment_instance.transaction_id
        refund_param["amount"] = amount
        refund_param["refund_id"] = refunded_payment_details.get("id")
        refund_param["receipt_number"] = refunded_payment_details.get("id")
        refund_param["razor_payment_id"] = refunded_payment_details.get("payment_id")
        refund_param["request_id"] = refunded_payment_details.get("payment_id")
        refund_instance = PaymentRefundSerializer(data=refund_param)
        refund_instance.is_valid(raise_exception=True)
        refund_instance.save()
    
    @staticmethod
    def update_failed_payment_response(payment_instance,order_details,order_payment_details,is_requested_from_mobile):
        
        payment_instance.uhid_number = PaymentUtils.get_uhid_number(payment_instance)
        payment_instance.status = PaymentConstants.MANIPAL_PAYMENT_STATUS_FAILED
        payment_instance.save()

        if order_details.get("status")==PaymentConstants.RAZORPAY_PAYMENT_STATUS_PAID and payment_instance.amount>0:
            hospital_key_info = PaymentUtils.get_hospital_key_info_from_payment_instance(payment_instance)
            hospital_key = hospital_key_info.secret_key
            hospital_secret = hospital_key_info.secret_secret
            refunded_payment_details = PaymentUtils.get_razorpay_payment_data_from_order_id(hospital_key,hospital_secret,order_details.get("id"),order_details)
            if not refunded_payment_details or refunded_payment_details.get("status") not in [PaymentConstants.RAZORPAY_PAYMENT_STATUS_REFUNDED]:
                refunded_payment_details = PaymentUtils.initiate_refund(
                    hospital_key=hospital_key,
                    hospital_secret=hospital_secret,
                    payment_id=order_payment_details.get("id"),
                    amount_to_be_refunded=int(payment_instance.amount)
                )
                if refunded_payment_details:
                    PaymentUtils.update_refund_payment_response(refunded_payment_details,payment_instance,int(payment_instance.amount))
                    
            payment_instance.status = PaymentConstants.MANIPAL_PAYMENT_STATUS_REFUNDED
            payment_instance.save()

        if is_requested_from_mobile:
            raise PaymentProcessingFailedRefundProcessedException
        else:
            raise PaymentProcessingFailedRefundProcessed

    @staticmethod
    def update_failed_payment_response_with_refund(payment_instance,order_details,order_payment_details,is_requested_from_mobile):
        if payment_instance.payment_for_uhid_creation and not payment_instance.appointment and not payment_instance.payment_for_health_package and not payment_instance.payment_for_drive:
            PaymentUtils.update_failed_payment_response(payment_instance,order_details,order_payment_details,is_requested_from_mobile)


    @staticmethod
    def create_or_update_unprocessed_trans_instance(unprocessed_transaction_data):

        unprocessed_trans_instance = None
        try:
            unprocessed_trans_instance = UnprocessedTransactions.objects.get(**unprocessed_transaction_data)
        except Exception as e:
            pass

        if not unprocessed_trans_instance:
            unprocessed_trans = UnprocessedTransactionsSerializer(data=unprocessed_transaction_data)
            unprocessed_trans.is_valid(raise_exception=True)
            unprocessed_trans_instance = unprocessed_trans.save()

    @staticmethod
    def update_failed_payment_response_without_refund(payment_instance,order_details,order_payment_details,is_requested_from_mobile):
        if payment_instance and (payment_instance.appointment or  payment_instance.payment_for_health_package or payment_instance.payment_for_op_billing or payment_instance.payment_for_ip_deposit):
            
            patient_instance,family_member_instance = PaymentUtils.get_patient_and_family_member_instance_from_payment_instance(payment_instance)
            payment_response = {
                "uhid_number":family_member_instance.uhid_number if family_member_instance else patient_instance.uhid_number,
                "appointment_identifier":None
            }
            
            appointment_instance = None
            health_package_appointment_instance = None

            if payment_instance.appointment:
                appointment_instance = Appointment.objects.filter(id=payment_instance.appointment.id).first()
                payment_response.update({
                    "appointment_identifier":appointment_instance.appointment_identifier
                })
            elif payment_instance.payment_for_health_package:
                health_package_appointment_instance = HealthPackageAppointment.objects.filter(id=payment_instance.health_package_appointment.id).first()
                payment_response.update({
                    "appointment_identifier":health_package_appointment_instance.appointment_identifier
                })
                
            PaymentUtils.update_payment_details(payment_instance,payment_response,order_details,order_payment_details,is_requested_from_mobile)
            PaymentUtils.payment_for_scheduling_appointment(payment_instance,payment_response,order_details,is_requested_from_mobile)
            PaymentUtils.payment_update_for_health_package(payment_instance,payment_response)

            unprocessed_transaction_data = {
                "payment"                   : payment_instance.id,
                "appointment"               : appointment_instance.id if appointment_instance else None,
                "health_package_appointment": health_package_appointment_instance.id if health_package_appointment_instance else None,
                "patient"                   : family_member_instance.patient_info.id if family_member_instance else patient_instance.id,
                "family_member"             : family_member_instance.id if family_member_instance else None
            }

            PaymentUtils.create_or_update_unprocessed_trans_instance(unprocessed_transaction_data)

    @staticmethod
    def get_payment_amount(order_details):
        if order_details.get("amount") and AMOUNT_OFFSET:
            return int(order_details.get("amount"))/int(AMOUNT_OFFSET)
        return order_details.get("amount")

    @staticmethod
    def get_payment_description(param,user=None):
        account_number = ""
        email = ""
        phone = ""
        name = ""
        if  param and \
            param.get("token") and \
            param.get("token").get("accounts") and \
            len(param.get("token").get("accounts"))>0:
                account_number = param["token"]["accounts"][0].get("account_number")
                email = param["token"]["accounts"][0].get("email")
                phone = param["token"]["accounts"][0].get("phone")
        if user:
            name = "%s %s"%(user.first_name or "",user.last_name or "")
        return "Name: %s; UHID: %s; email: %s; contact: %s"%(name,account_number,email,str(phone))

    @staticmethod
    def set_param_for_appointment(param,appointment):
        if "token" not in param:
            param["token"] = {}
        param["token"]["appointment_id"] = appointment
        param["token"]["package_code"] = PaymentConstants.APPOINTMENT_PACKAGE_CODE
        param["token"]["transaction_type"] = PaymentConstants.APPOINTMENT_TRANSACTION_TYPE
        return param
    
    @staticmethod
    def set_param_for_drive_booking(param,drive_id):
        if "token" not in param:
            param["token"] = {}
        param["token"]["drive_id"] = drive_id
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
    def set_payment_data_for_drive_booking(request,param,drive_booking_instance,hospital):
        payment_data = {}
        payment_data["processing_id"] = param["token"]["processing_id"]
        payment_data["patient"] = drive_booking_instance.patient
        payment_data["payment_done_for_patient"] = drive_booking_instance.patient
        payment_data["payment_for_drive"] = True
        payment_data["location"] = hospital.id
        payment_data["amount"] = param["token"]["accounts"][0]["amount"]
        if drive_booking_instance.family_member:
            payment_data["payment_done_for_patient"] = None
            payment_data["payment_done_for_family_member"] = drive_booking_instance.family_member.id
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
        promo_code = DoctorChargesSerializer.get_promo_code(appointment_instance.doctor)
        response_doctor_charges = client.post(
                                        PaymentConstants.URL_CONSULTATION_CHARGES,
                                        json.dumps({
                                            'location_code': location_code, 
                                            'specialty_code': appointment_instance.department.code, 
                                            'doctor_code': appointment_instance.doctor.code, 
                                            "uhid":uhid, 
                                            'order_date': order_date,
                                            "promo_code":promo_code
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
    def fetch_item_price(drive_instance,drive_inventory_instance,location_code):
        response_item_price_response = client.post(
                                        PaymentConstants.URL_GET_ITEM_PRICE,
                                        json.dumps({
                                            'location_code': location_code, 
                                            'item_code': drive_inventory_instance.mh_item_code, 
                                            'order_date': drive_instance.date.strftime("%d/%m/%Y")
                                        }), 
                                        content_type=PaymentConstants.JSON_CONTENT_TYPE
                                    )
        item_price = None
        response_item_price = response_item_price_response.data
        if  response_item_price and \
            response_item_price.get("data") and \
            response_item_price.get("data").get("OrderItemPrice") and \
            response_item_price.get("data").get("OrderItemPrice")[0] and \
            "ItemPrice" in response_item_price.get("data").get("OrderItemPrice")[0]:
            item_price = response_item_price.get("data").get("OrderItemPrice")[0].get("ItemPrice")
        
        if item_price is None:
            raise ValidationError("Could not fetch item price.")
        
        return item_price

    @staticmethod
    def calculate_amount_for_drive(drive_instance,drive_inventory_instance,location_code,is_registration_payment):
        total_amount = 0
        item_price = PaymentUtils.fetch_item_price(drive_instance,drive_inventory_instance,location_code)
        total_amount += item_price

        drive_billing_ids = DriveBilling.objects.filter(drive__id=drive_instance.id)
        for drive_billing_id  in drive_billing_ids:
            if drive_billing_id.billing.code!="registration" or is_registration_payment:
                total_amount += drive_billing_id.price
                
        return total_amount
    
    @staticmethod
    def validate_order_amount_for_drive_booking(request,drive_booking_instance,location_code,param):
        is_registration_payment =  request.data.get("registration_payment", False)
        drive_instance = drive_booking_instance.drive
        drive_inventory_instance = drive_booking_instance.drive_inventory
        calculated_amount = PaymentUtils.calculate_amount_for_drive(drive_instance,drive_inventory_instance,location_code,is_registration_payment)
        
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
    def set_order_id_for_appointments(param,payment_data,user):
        hospital_key = param["token"]["auth"]["key"]
        hospital_secret = param["token"]["auth"].pop("secret")
        amount = int(float(param["token"]["accounts"][0]["amount"]))
        description = PaymentConstants.RAZORPAY_APPOINTMENT_PAYMENT_DESCRIPTION +"; "+ PaymentUtils.get_payment_description(param,user)
        currency = PaymentConstants.RAZORPAY_PAYMENT_CURRENCY
        order_id = PaymentUtils.create_razorpay_order_id(
                                    hospital_key=hospital_key,
                                    hospital_secret=hospital_secret,
                                    amount=amount,
                                    description=description,
                                    currency=currency
                                )
        param["token"]["order_id"] = order_id
        payment_data["razor_order_id"] = order_id
        return param,payment_data

    @staticmethod
    def set_order_id_for_drive_booking(param,payment_data,user):
        hospital_key = param["token"]["auth"]["key"]
        hospital_secret = param["token"]["auth"].pop("secret")
        amount = int(float(param["token"]["accounts"][0]["amount"]))
        description = PaymentConstants.RAZORPAY_DRIVE_BOOKING_PAYMENT_DESCRIPTION +"; "+ PaymentUtils.get_payment_description(param,user)
        currency = PaymentConstants.RAZORPAY_PAYMENT_CURRENCY
        order_id = PaymentUtils.create_razorpay_order_id(
                                    hospital_key=hospital_key,
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
    def set_payment_data_for_health_package(request,param,hospital,appointment_instance):
        payment_data = {}
        payment_data["processing_id"] = param.get("token").get("processing_id")
        payment_data["patient"] = request.user.id
        payment_data["location"] = hospital.id
        payment_data["health_package_appointment"] = appointment_instance.id
        payment_data["payment_for_health_package"] = True
        registration_payment = request.data.get("registration_payment", False)
        if registration_payment:
            payment_data["payment_for_uhid_creation"] = True
        family_member = request.data.get("user_id", None)
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
    def set_order_id_for_health_package(param,payment_data,user):
        hospital_key = param["token"]["auth"]["key"]
        hospital_secret = param["token"]["auth"].pop("secret")
        amount = int(float(param["token"]["accounts"][0]["amount"]))
        description = PaymentConstants.RAZORPAY_HEALTH_PACKAGE_PURCHASE_DESCRIPTION +"; "+ PaymentUtils.get_payment_description(param,user)
        currency = PaymentConstants.RAZORPAY_PAYMENT_CURRENCY
        order_id = PaymentUtils.create_razorpay_order_id(
                                    hospital_key=hospital_key,
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
    def set_payment_data_for_uhid(request,param,hospital):
        payment_data = {}
        payment_data["processing_id"] = param["token"]["processing_id"]
        payment_data["patient"] = request.user.id
        payment_data["location"] = hospital.id
        family_member = request.data.get("user_id", None)
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
    def set_order_id_for_uhid(param,payment_data,user):
        hospital_key = param["token"]["auth"]["key"]
        hospital_secret = param["token"]["auth"].pop("secret")
        amount = int(float(param["token"]["accounts"][0]["amount"]))
        description = PaymentConstants.RAZORPAY_UHID_PURCHASE_DESCRIPTION +"; "+ PaymentUtils.get_payment_description(param,user)
        currency = PaymentConstants.RAZORPAY_PAYMENT_CURRENCY
        order_id = PaymentUtils.create_razorpay_order_id(
                                    hospital_key=hospital_key,
                                    hospital_secret=hospital_secret,
                                    amount=amount,
                                    description=description,
                                    currency=currency
                                )
        param["token"]["order_id"] = order_id
        payment_data["razor_order_id"] = order_id
        return param,payment_data




    


    

    @staticmethod
    def set_param_for_op_bill(param,location_code,episode_no,bill_row_id):
        if "token" not in param:
            param["token"] = {}
        param["token"]["transaction_type"] = PaymentConstants.OP_BILL_TRANSACTION_TYPE
        param["token"]["appointment_id"] = episode_no
        param["token"]["payment_location"] = location_code
        param["token"]["bill_row_id"] = bill_row_id
        return param

    @staticmethod
    def set_payment_data_for_op_bill(request,param,hospital,episode_no,bill_row_id):
        payment_data = {}
        payment_data["processing_id"] = param["token"]["processing_id"]
        payment_data["patient"] = request.user.id
        payment_data["location"] = hospital.id
        family_member = request.data.get("user_id", None)
        if family_member is not None:
            payment_data["payment_done_for_family_member"] = family_member
        else:
            payment_data["payment_done_for_patient"] = request.user.id
        payment_data["payment_for_op_billing"] = True
        payment_data["episode_number"] = episode_no
        payment_data["bill_row_id"] = bill_row_id
        
        return payment_data

    @staticmethod
    def validate_order_amount_for_op_bill(param,location_code,episode_no,bill_row_id):
        calculated_amount = 0
        response = client.post(
                        PaymentConstants.URL_OP_BILL_DETAILS,
                        json.dumps({
                            "uhid": param["token"]["accounts"][0]["account_number"], 
                            'location_code': location_code
                        }), 
                        content_type=PaymentConstants.JSON_CONTENT_TYPE
                    )
        if  response.status_code == 200 and \
            response.data and \
            response.data.get("success") == True and \
            response.data.get("data"):
            episode_list = response.data.get("data")
            for episode in episode_list:
                if episode.get("EpisodeNo") == episode_no and episode.get("BillRowId") == bill_row_id:
                    calculated_amount += int(float(episode["OutStandingAmt"]))
                    
        if not (calculated_amount == int(float(param["token"]["accounts"][0]["amount"]))):
            raise ValidationError(PaymentConstants.ERROR_MESSAGE_PRICE_UPDATED)

    @staticmethod
    def set_order_id_for_op_bill(param,payment_data,user):
        hospital_key = param["token"]["auth"]["key"]
        hospital_secret = param["token"]["auth"].pop("secret")
        amount = int(float(param["token"]["accounts"][0]["amount"]))
        description = PaymentConstants.RAZORPAY_OP_BILL_PAYMENT_DESCRIPTION +"; "+ PaymentUtils.get_payment_description(param,user)
        currency = PaymentConstants.RAZORPAY_PAYMENT_CURRENCY
        order_id = PaymentUtils.create_razorpay_order_id(
                                    hospital_key=hospital_key,
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
    def set_payment_data_for_ip_deposit(request,param,hospital):
        payment_data = {}
        payment_data["processing_id"] = param["token"]["processing_id"]
        payment_data["patient"] = request.user.id
        payment_data["location"] = hospital.id
        family_member = request.data.get("user_id", None)
        if family_member is not None:
            payment_data["payment_done_for_family_member"] = family_member
        else:
            payment_data["payment_done_for_patient"] = request.user.id
        payment_data["payment_for_ip_deposit"] = True
        return payment_data

    @staticmethod
    def set_order_id_for_ip_deposit(param,payment_data,user):
        hospital_key = param["token"]["auth"]["key"]
        hospital_secret = param["token"]["auth"].pop("secret")
        amount = int(float(param["token"]["accounts"][0]["amount"]))
        description = PaymentConstants.RAZORPAY_IP_DEPOSIT_PAYMENT_DESCRIPTION +"; "+ PaymentUtils.get_payment_description(param,user)
        currency = PaymentConstants.RAZORPAY_PAYMENT_CURRENCY
        order_id = PaymentUtils.create_razorpay_order_id(
                                    hospital_key=hospital_key,
                                    hospital_secret=hospital_secret,
                                    amount=amount,
                                    description=description,
                                    currency=currency
                                )
        param["token"]["order_id"] = order_id
        payment_data["razor_order_id"] = order_id
        return param,payment_data




    @staticmethod
    def get_appointment_plan_code(payment_instance):
        plan_code = ""
        if payment_instance.appointment:
            appointment_instance = Appointment.objects.filter(id=payment_instance.appointment.id).first()
            plan_code = appointment_instance.plan_code
        # elif payment_instance.payment_for_health_package:
        #     appointment_instance = HealthPackageAppointment.objects.filter(id=payment_instance.health_package_appointment.id).first()
        return plan_code
    
    @staticmethod
    def get_appointment_instance_from_payment_instance(payment_instance):
        appointment_instance = None
        if payment_instance.appointment:
            appointment_instance = Appointment.objects.filter(id=payment_instance.appointment.id).first()
        elif payment_instance.payment_for_health_package:
            appointment_instance = HealthPackageAppointment.objects.filter(id=payment_instance.health_package_appointment.id).first()
        return appointment_instance

    @staticmethod
    def get_patient_instance_from_payment_instance(payment_instance):
        patient_instance = None
        if payment_instance.payment_done_for_patient:
            patient_instance = Patient.objects.filter(id=payment_instance.payment_done_for_patient.id).first()
        elif payment_instance.payment_done_for_family_member:
            patient_instance = FamilyMember.objects.filter(id=payment_instance.payment_done_for_family_member.id).first()
        return patient_instance

    @staticmethod
    def get_patient_and_family_member_instance_from_payment_instance(payment_instance):
        patient_instance = None
        family_member_instance = None
        if payment_instance.payment_done_for_patient:
            patient_instance = Patient.objects.filter(id=payment_instance.payment_done_for_patient.id).first()
        if payment_instance.payment_done_for_family_member:
            family_member_instance = FamilyMember.objects.filter(id=payment_instance.payment_done_for_family_member.id).first()
            patient_instance = family_member_instance.patient_info
        return patient_instance,family_member_instance

    @staticmethod
    def validate_uhid_number(uhid_number):
        if uhid_number and len(uhid_number)>2 and (uhid_number[:2].upper() == "MH" or uhid_number[:3].upper() == "MMH"):
            return True
        return False

    @staticmethod
    def get_bill_details(payment_response,bill_detail_label,api_type):
        if not payment_response:
            return payment_response
        payment_paydetail = payment_response[api_type]
        bill_detail = {}
        if payment_paydetail[bill_detail_label]:
            bill_detail = json.loads(payment_paydetail[bill_detail_label])[0]
        return bill_detail

    @staticmethod
    def get_payment_method_from_order_payment_details(order_payment_details):
        payment_method = ""
        if order_payment_details.get('method'):
            payment_method += order_payment_details.get('method')
        if order_payment_details.get("bank"):
            payment_method += " "+order_payment_details.get("bank")
        if order_payment_details.get("wallet"):
            payment_method += " "+order_payment_details.get("wallet")
        if order_payment_details.get("vpa"):
            payment_method += " "+order_payment_details.get("vpa")
        return payment_method

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
    def get_pre_registration_number(payment_instance):
        patient_instance = PaymentUtils.get_patient_instance_from_payment_instance(payment_instance)
        return str(patient_instance.pre_registration_number) if patient_instance and patient_instance.pre_registration_number else ""
    
    @staticmethod
    def get_patients_mobile_number(payment_instance):
        patient_instance = PaymentUtils.get_patient_instance_from_payment_instance(payment_instance)
        return str(patient_instance.mobile) if patient_instance and patient_instance.mobile else ""
    
    @staticmethod
    def get_patients_email_id(payment_instance):
        patient_instance = PaymentUtils.get_patient_instance_from_payment_instance(payment_instance)
        return str(patient_instance.email) if patient_instance and patient_instance.email else ""
    
    @staticmethod
    def get_patients_name(payment_instance):
        patient_instance = PaymentUtils.get_patient_instance_from_payment_instance(payment_instance)
        return str(patient_instance.first_name) if patient_instance and patient_instance.first_name else ""

    @staticmethod
    def get_appointment_type(payment_instance):
        appointment_type = ""
        if payment_instance.payment_for_health_package:
            appointment_type = "H"
        elif payment_instance.appointment:
            appointment_type = "A"
        return appointment_type

    @staticmethod
    def get_health_package_appointment_code(payment_instance):
        hp_codes = []
        if payment_instance.health_package_appointment:
            appointment_instance = HealthPackageAppointment.objects.filter(id=payment_instance.health_package_appointment.id).first()
            if appointment_instance and appointment_instance.health_package:
                for health_package in appointment_instance.health_package.all():
                    if health_package.code:
                        hp_codes.append(health_package.code)
        return "||".join(hp_codes) if hp_codes else "NA"

    @staticmethod
    def get_episode_number_for_op_bill(payment_instance):
        episode_numbers = ""
        if payment_instance.episode_number:
            episode_numbers = payment_instance.episode_number
        return episode_numbers

    @staticmethod
    def get_bill_row_id_for_op_bill(payment_instance):
        bill_row_id = ""
        if payment_instance.bill_row_id:
            bill_row_id = payment_instance.bill_row_id
        return bill_row_id

    @staticmethod
    def get_uhid_number(payment_instance):
        uhid_number = ""
        patient_instance = PaymentUtils.get_patient_instance_from_payment_instance(payment_instance)
        if patient_instance:
            if patient_instance.uhid_number:
                uhid_number = str(patient_instance.uhid_number)
            elif patient_instance.pre_registration_number:
                uhid_number = str(patient_instance.pre_registration_number)
        return uhid_number

    @staticmethod
    def get_aadhar_number(payment_instance):
        aadhar_number = ""
        patient_instance = PaymentUtils.get_patient_instance_from_payment_instance(payment_instance)
        if patient_instance and payment_instance.appointment and patient_instance.aadhar_number:
            aadhar_number = str(patient_instance.aadhar_number)
        return aadhar_number
    
    @staticmethod
    def get_drive_patients_aadhar_number(payment_instance):
        aadhar_number = ""
        patient_instance = PaymentUtils.get_patient_instance_from_payment_instance(payment_instance)
        if patient_instance and patient_instance.aadhar_number:
            aadhar_number = str(patient_instance.aadhar_number)
        return aadhar_number

    @staticmethod
    def get_appointment_identifier(payment_instance):
        appointment_instance = PaymentUtils.get_appointment_instance_from_payment_instance(payment_instance)
        return appointment_instance.appointment_identifier if appointment_instance and appointment_instance.appointment_identifier else ""

    @staticmethod
    def get_beneficiary_reference_id(payment_instance):
        appointment_instance = PaymentUtils.get_appointment_instance_from_payment_instance(payment_instance)
        return appointment_instance.beneficiary_reference_id if payment_instance.appointment and appointment_instance and appointment_instance.beneficiary_reference_id else ""
    
    @staticmethod
    def get_total_service_charges(drive_booking):
        total_price = 0
        drive_billing_ids = DriveBilling.objects.filter(drive__id=drive_booking.drive.id)
        if drive_billing_ids.exists():
            for drive_billing_id in drive_billing_ids:
                if drive_billing_id.billing.code!="registration":
                    total_price += drive_billing_id.price
        return int(total_price)

    @staticmethod
    def get_registration_charges(drive_booking):
        total_price = 0
        drive_billing_ids = DriveBilling.objects.filter(drive__id=drive_booking.drive.id)
        if drive_billing_ids.exists():
            for drive_billing_id in drive_billing_ids:
                if drive_billing_id.billing.code=="registration":
                    total_price += drive_billing_id.price
        return int(total_price)

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
    def set_receipt_number_for_only_uhid(payment_instance,bill_details,payment):
        if  payment_instance.payment_for_uhid_creation and \
            not payment_instance.appointment and \
            not payment_instance.payment_for_health_package and \
            not payment_instance.payment_for_drive and \
            bill_details.get("ReceiptNo"):

            payment["receipt_number"] = bill_details.get("ReceiptNo")

        return payment

    @staticmethod
    def set_receipt_number_for_app_hp_ip(payment_instance,bill_details,payment,is_requested_from_mobile):
        if  payment_instance.appointment or \
            payment_instance.payment_for_health_package or \
            payment_instance.payment_for_ip_deposit:

            if not bill_details.get("ReceiptNo") and not is_requested_from_mobile:
                raise ReceiptGenerationFailedException

            if bill_details.get("ReceiptNo"):
                payment["receipt_number"] = bill_details.get("ReceiptNo")

        return payment

    @staticmethod
    def set_receipt_number_for_op(payment_instance,bill_details,payment):
        if payment_instance.payment_for_op_billing:
            if not bill_details.get("BillNo"):
                raise ReceiptGenerationFailedException
            payment["receipt_number"] = bill_details.get("BillNo")
            if bill_details.get("EpisodeNo"):
                payment["episode_number"] = bill_details.get("EpisodeNo")

        return payment
    
    @staticmethod
    def set_receipt_number_for_drive(payment_instance,order_payment_details,payment):
        if payment_instance.payment_for_drive:
            payment["receipt_number"] = order_payment_details.get("invoice_id")
        return payment

    @staticmethod
    def set_receipt_number(payment_instance,bill_details,payment,is_requested_from_mobile,order_payment_details):

        payment = PaymentUtils.set_receipt_number_for_only_uhid(payment_instance,bill_details,payment)
        payment = PaymentUtils.set_receipt_number_for_app_hp_ip(payment_instance,bill_details,payment,is_requested_from_mobile)
        payment = PaymentUtils.set_receipt_number_for_op(payment_instance,bill_details,payment)
        payment = PaymentUtils.set_receipt_number_for_drive(payment_instance,order_payment_details,payment)

        return payment



    
    @staticmethod
    def update_payment_details(payment_instance,payment_response,order_details,order_payment_details,is_requested_from_mobile):
        payment = {}
        payment = PaymentUtils.set_receipt_number(payment_instance,payment_response,payment,is_requested_from_mobile,order_payment_details)
        payment["uhid_number"] = payment_response.get("uhid_number")
        payment["razor_payment_id"] = order_payment_details.get("id")
        payment["razor_invoice_id"] = order_payment_details.get("invoice_id")
        payment["payment_method"] = PaymentUtils.get_payment_method_from_order_payment_details(order_payment_details)
        payment["transaction_id"] = order_payment_details.get("id")
        payment["status"] = PaymentConstants.MANIPAL_PAYMENT_STATUS_SUCCESS
        payment["amount"] = PaymentUtils.get_payment_amount(order_details)
        payment_serializer = PaymentSerializer(payment_instance, data=payment, partial=True)
        payment_serializer.is_valid(raise_exception=True)
        payment_serializer.save()

        patient_instance = PaymentUtils.get_patient_instance_from_payment_instance(payment_instance)
        if payment_response.get("uhid_number") and not patient_instance.uhid_number:
            patient_instance.uhid_number = payment_response.get("uhid_number")
            patient_instance.save()

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
    def payment_for_uhid_creation_method(payment_instance,payment_response):
        uhid_info = {"uhid_number":payment_response.get("uhid_number")}
        if payment_instance and payment_instance.payment_for_uhid_creation:
            PaymentUtils.payment_for_uhid_creation_appointment(payment_instance)
            PaymentUtils.payment_for_uhid_creation_payment_done_for_patient(payment_instance,uhid_info)
            PaymentUtils.payment_for_uhid_creation_payment_done_for_family_member(payment_instance,uhid_info)

    @staticmethod
    def payment_for_scheduling_appointment(payment_instance,payment_response,order_details,is_requested_from_mobile):
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
            appointment_instance = appointment_serializer.save()
            if not is_requested_from_mobile and appointment_instance.appointment_mode in ["VC", "PR"]:
                send_appointment_invitation(appointment_instance)

    @staticmethod
    def payment_update_for_health_package(payment_instance,payment_response):
        if payment_instance.payment_for_health_package:
            appointment_instance = HealthPackageAppointment.objects.filter(id=payment_instance.health_package_appointment.id).first()
            update_data = {
                "payment" : payment_instance.id,
                "appointment_identifier" : payment_response.get("appointment_identifier"),
                "appointment_status":PaymentConstants.HEALTH_PACKAGE_APPOINTMENT_STATUS_BOOKED
            }
            appointment_serializer = HealthPackageAppointmentSerializer(appointment_instance, data=update_data, partial=True)
            appointment_serializer.is_valid(raise_exception=True)
            appointment_serializer.save()

    @staticmethod
    def payment_update_for_drive_booking(payment_instance):
        if payment_instance.payment_for_drive:
            drive_booking_instance = DriveBooking.objects.get(payment__id=payment_instance.id)
            update_data = {
                "status":DriveBooking.BOOKING_BOOKED
            }
            drive_booking_serializer = DriveBookingSerializer(drive_booking_instance, data=update_data, partial=True)
            drive_booking_serializer.is_valid(raise_exception=True)
            drive_booking_serializer.save()


    @staticmethod
    def cancel_drive_booking_on_failure(payment_instance):
        if payment_instance.payment_for_drive:
            drive_booking_instance = DriveBooking.objects.get(payment__id=payment_instance.id)
            update_data = {
                "status":DriveBooking.BOOKING_CANCELLED
            }
            drive_booking_serializer = DriveBookingSerializer(drive_booking_instance, data=update_data, partial=True)
            drive_booking_serializer.is_valid(raise_exception=True)
            drive_booking_serializer.save()


    @staticmethod
    def manage_appointment_payment(aap_list,app_id):
        success_status = False
        if aap_list and len(aap_list)>0:
            appointment_identifier = aap_list[0].get("AppointmentId")
            appointment_instance = Appointment.objects.filter(appointment_identifier=app_id).first()
            if appointment_instance:
                success_status = True
                appointment_instance.payment_status = "success"
                if appointment_identifier:
                    appointment_instance.appointment_identifier = appointment_identifier
                appointment_instance.save()
        return success_status

    @staticmethod
    def serialize_payment_response(bill_details_response):
        payment_response = dict()
        if not bill_details_response.get("HospitalNo"):
            raise UHIDRegistrationFailedException
        if not PaymentUtils.validate_uhid_number(bill_details_response.get("HospitalNo")):
            raise InvalidGeneratedUHIDException
        if not bill_details_response.get("ReceiptNo"):
            raise ReceiptGenerationFailedException
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
    def serialize_opbill_payment_response(bill_details_response):
        payment_response = dict()
        if not bill_details_response.get("HospitalNo"):
            raise UHIDRegistrationFailedException
        if not PaymentUtils.validate_uhid_number(bill_details_response.get("HospitalNo")):
            raise InvalidGeneratedUHIDException
        if not bill_details_response.get("BillNo"):
            raise BillNoNotGeneratedAvailable
        payment_response.update({
            "uhid_number"   :bill_details_response.get("HospitalNo"),
            "hospital_code" :bill_details_response.get("Hosp"),
            "BillNo"        :bill_details_response.get("BillNo"),
            "BillAmount"    :bill_details_response.get("BillAmount"),
            "PaidAmt"       :bill_details_response.get("PaidAmt"),
            "EpisodeNo"     :bill_details_response.get("EpisodeNo")
        })
        return payment_response

    @staticmethod
    def serialize_ipdeposit_payment_response(bill_details_response):
        payment_response = dict()
        if not bill_details_response.get("HospitalNo"):
            raise UHIDRegistrationFailedException
        if not PaymentUtils.validate_uhid_number(bill_details_response.get("HospitalNo")):
            raise InvalidGeneratedUHIDException
        if not bill_details_response.get("ReceiptNo"):
            raise ReceiptGenerationFailedException

        if bill_details_response.get("Hosp"):
            payment_response.update({"hospital_code" :bill_details_response.get("Hosp")})
        if bill_details_response.get("DepositAmount"):
            payment_response.update({"DepositAmount" :bill_details_response.get("DepositAmount")})
            
        payment_response.update({
            "uhid_number"   : bill_details_response.get("HospitalNo"),
            "ReceiptNo"     : bill_details_response.get("ReceiptNo")
        })
        return payment_response
    
    @staticmethod
    def serialize_drive_booking_payment_response(bill_details_response):
        payment_response = dict()
        if not bill_details_response.get("HospitalNo"):
            raise UHIDRegistrationFailedException
        if not PaymentUtils.validate_uhid_number(bill_details_response.get("HospitalNo")):
            raise InvalidGeneratedUHIDException
        if not bill_details_response.get("ReceiptNo"):
            raise ReceiptGenerationFailedException

        if bill_details_response.get("Hosp"):
            payment_response.update({"hospital_code" :bill_details_response.get("Hosp")})
            
        payment_response.update({
            "uhid_number"   : bill_details_response.get("HospitalNo"),
            "ReceiptNo"     : bill_details_response.get("ReceiptNo")
        })
        return payment_response

    @staticmethod
    def serialize_check_appointment_payment_status_response(payment_check_response,appointment_id):
        payment_response = dict()
        
        if  not payment_check_response or \
            not payment_check_response.get("Status") or \
            payment_check_response.get("Status")==PaymentConstants.CHECK_APPOINTMENT_PAYMENT_STATUS_FAILED:
            return payment_response
        
        if  payment_check_response.get("Status")==PaymentConstants.CHECK_APPOINTMENT_PAYMENT_STATUS_SUCCESS and \
            payment_check_response.get("APPOLPReceiptNo") and \
            payment_check_response.get("APPOLPPatHospNo") and \
            payment_check_response.get("APPOLPConvAppId"):
            
            payment_response.update({
                "uhid_number"           : payment_check_response.get("APPOLPPatHospNo"),
                "ReceiptNo"             : payment_check_response.get("APPOLPReceiptNo"),
                "appointment_identifier": payment_check_response.get("APPOLPConvAppId"),
                "StatusMessage"         : PaymentConstants.MANIPAL_PAYMENT_STATUS_SUCCESS,
            })
        
        return payment_response


    @staticmethod
    def check_appointment_payment_status(payment_instance):
        appointment_id = PaymentUtils.get_appointment_identifier(payment_instance)
        payment_check_request = {
            "appointment_id":appointment_id,
            "location_code":payment_instance.location.code
        }
        payment_check_response = CheckAppointmentPaymentStatusView.as_view()(cancel_and_refund_parameters(payment_check_request))
        
        if  not payment_check_response.status_code==200 or \
            not payment_check_response.data or \
            not payment_check_response.data.get("data"):
            raise InvalidResponseFromManipalServers
        payment_response = payment_check_response.data.get("data")
        
        return PaymentUtils.serialize_check_appointment_payment_status_response(payment_response,appointment_id)

    @staticmethod
    def update_uhid_payment_details_with_manipal(payment_instance,order_details,order_payment_details,pay_mode="",amount=None):
        payment_update_request = {
            "location_code":payment_instance.location.code,
            "temp_id":PaymentUtils.get_pre_registration_number(payment_instance),
            "transaction_number":order_details.get("id"),
            "gateway_id":order_payment_details.get("id"),
            "amt":str(amount) if amount is not None else str(PaymentUtils.get_payment_amount(order_details)),
            "mobile":PaymentUtils.get_patients_mobile_number(payment_instance),
            "pay_mode":pay_mode
        }
        payment_update_response = UHIDPaymentView.as_view()(cancel_and_refund_parameters(payment_update_request))
        if payment_update_response and payment_update_response.data:
            payment_instance.raw_info_from_manipal_response = json.dumps(payment_update_response.data)
            payment_instance.save()
        if  not payment_update_response.status_code==200 or \
            not payment_update_response.data or \
            not payment_update_response.data.get("data"):
            raise InvalidResponseFromManipalServers
        
        payment_response = payment_update_response.data.get("data")
        PaymentUtils.validate_uhid_number(payment_response.get("uhid_number"))
        return payment_response

    @staticmethod
    def update_payment_details_with_manipal(payment_instance,order_details,order_payment_details):
        payment_update_request = {
            "uhid":PaymentUtils.get_uhid_number(payment_instance),
            "transaction_number":order_payment_details.get('id'),
            "processing_id":order_details.get("id"),
            "amt":str(PaymentUtils.get_payment_amount(order_details)),
            "location_code":payment_instance.location.code,
            "app_date":PaymentUtils.get_payment_appointment_date(payment_instance),
            "package_code":PaymentUtils.get_health_package_appointment_code(payment_instance),
            "plan_code":PaymentUtils.get_appointment_plan_code(payment_instance),
            "type":PaymentUtils.get_appointment_type(payment_instance),
            "app_id":PaymentUtils.get_appointment_identifier(payment_instance),
            "aadhar_number":PaymentUtils.get_aadhar_number(payment_instance),
            "beneficiary_reference_id":PaymentUtils.get_beneficiary_reference_id(payment_instance)
        }
        payment_update_response = AppointmentPaymentView.as_view()(cancel_and_refund_parameters(payment_update_request))
        if payment_update_response and payment_update_response.data:
            payment_instance.raw_info_from_manipal_response = json.dumps(payment_update_response.data)
            payment_instance.save()
        if  not payment_update_response.status_code==200 or \
            not payment_update_response.data or \
            not payment_update_response.data.get("data"):
            raise InvalidResponseFromManipalServers
        bill_details_response = PaymentUtils.get_bill_details(payment_update_response.data.get("data"),"BillDetail","payDetailAPIResponse")
        return PaymentUtils.serialize_payment_response(bill_details_response)

    @staticmethod
    def update_op_bill_payment_details_with_manipal(payment_instance,order_details,order_payment_details):
        payment_update_request = {
            "uhid":PaymentUtils.get_uhid_number(payment_instance),
            "transaction_number":order_payment_details.get('id'),
            "processing_id":order_details.get("id"),
            "amt":str(PaymentUtils.get_payment_amount(order_details)),
            "location_code":payment_instance.location.code,
            "episode_number":PaymentUtils.get_episode_number_for_op_bill(payment_instance),
            "gateway_id":PaymentUtils.get_bill_row_id_for_op_bill(payment_instance)
        }
        payment_update_response = OPBillingPaymentView.as_view()(cancel_and_refund_parameters(payment_update_request))
        if payment_update_response and payment_update_response.data:
            payment_instance.raw_info_from_manipal_response = json.dumps(payment_update_response.data)
            payment_instance.save()
        if  not payment_update_response.status_code==200 or \
            not payment_update_response.data or \
            not payment_update_response.data.get("data"):
            raise InvalidResponseFromManipalServers
        bill_details_response = PaymentUtils.get_bill_details(payment_update_response.data.get("data"),"BillDetail","payDetailAPIResponse")
        return PaymentUtils.serialize_opbill_payment_response(bill_details_response)
    
    @staticmethod
    def update_ip_deposit_payment_details_with_manipal(payment_instance,order_details,order_payment_details):
        payment_update_request = {
            "uhid":PaymentUtils.get_uhid_number(payment_instance),
            "transaction_number":order_payment_details.get('id'),
            "auth_code":order_details.get("id"),
            "amt":str(PaymentUtils.get_payment_amount(order_details)),
            "location_code":payment_instance.location.code
        }
        payment_update_response = IPDepositPaymentView.as_view()(cancel_and_refund_parameters(payment_update_request))
        if payment_update_response and payment_update_response.data:
            payment_instance.raw_info_from_manipal_response = json.dumps(payment_update_response.data)
            payment_instance.save()
        if  not payment_update_response.status_code==200 or \
            not payment_update_response.data or \
            not payment_update_response.data.get("data"):
            raise InvalidResponseFromManipalServers
        bill_details_response = PaymentUtils.get_bill_details(payment_update_response.data.get("data"),"RecieptNumber","payDetailAPIResponse")
        return PaymentUtils.serialize_ipdeposit_payment_response(bill_details_response)

    @staticmethod
    def update_drive_booking_payment_details_with_manipal(payment_instance,order_details,order_payment_details,drive_booking):
        
        payment_update_request = {
            "location_code":payment_instance.location.code,
            "uhid":PaymentUtils.get_uhid_number(payment_instance),
            "email_id":PaymentUtils.get_patients_email_id(payment_instance),
            "mobile_no":PaymentUtils.get_patients_mobile_number(payment_instance),
            "transaction_id":order_payment_details.get('id'),
            "payment_status":"captured",
            "payment_date":date.today().strftime("%Y-%m-%d"),
            "order_id":order_details.get("id"),
            "aadhar_number":PaymentUtils.get_drive_patients_aadhar_number(payment_instance),
            "cowin_number":drive_booking.beneficiary_reference_id,
            "vaccination_date":drive_booking.drive.date.strftime("%Y-%m-%d"),
            "vaccination_dose":drive_booking.drive_inventory.dose,
            "vaccination_name":drive_booking.drive_inventory.medicine.name,
            "apartment_name":drive_booking.drive.description,
            "vaccination_item_code":drive_booking.drive_inventory.mh_item_code,
            "vaccination_charges":str(int(drive_booking.drive_inventory.price)),
            "medical_service_charges":str(PaymentUtils.get_total_service_charges(drive_booking)),
            "total_paid_amt":str(PaymentUtils.get_payment_amount(order_details)),
            "post_flag":"0",
            "resource":"PatientApp",
            "name":PaymentUtils.get_patients_name(payment_instance)
        }
        payment_update_response = DriveRegistrationPaymentStatusView.as_view()(cancel_and_refund_parameters(payment_update_request))
        if payment_update_response and payment_update_response.data:
            payment_instance.raw_info_from_manipal_response = payment_update_response.data
            payment_instance.save()

        return payment_update_response.data

    @staticmethod
    def wait_for_manipal_response(payment_instance,order_details):
        payment_check_response = dict()
        retry_count = 0
        while retry_count<5 and not payment_check_response:
            payment_check_response = PaymentUtils.check_appointment_payment_status(payment_instance)
            if not payment_check_response:
                time.sleep(5)
            retry_count += 1
        order_payment_details = PaymentUtils.get_razorpay_fetch_order_payments_payment_instance(order_details,payment_instance)
        if order_payment_details.get("status") in [PaymentConstants.RAZORPAY_PAYMENT_STATUS_REFUNDED]:
            raise PaymentProcessingFailedRefundProcessed
        return payment_check_response


    @staticmethod
    def update_manipal_on_payment(is_requested_from_mobile,payment_instance,order_details,order_payment_details):
        if payment_instance.payment_for_uhid_creation and not payment_instance.appointment and not payment_instance.payment_for_health_package and not payment_instance.payment_for_drive:
            return PaymentUtils.update_uhid_payment_details_with_manipal(payment_instance,order_details,order_payment_details)
        elif payment_instance.appointment or payment_instance.payment_for_health_package:
            payment_check_response = PaymentUtils.wait_for_manipal_response(payment_instance,order_details) if is_requested_from_mobile else PaymentUtils.check_appointment_payment_status(payment_instance)
            if payment_check_response:
                return payment_check_response
            return PaymentUtils.update_payment_details_with_manipal(payment_instance,order_details,order_payment_details)
        elif payment_instance.payment_for_op_billing:
            return PaymentUtils.update_op_bill_payment_details_with_manipal(payment_instance,order_details,order_payment_details)
        elif payment_instance.payment_for_ip_deposit:
            return PaymentUtils.update_ip_deposit_payment_details_with_manipal(payment_instance,order_details,order_payment_details)
        elif payment_instance.payment_for_drive:
            payment_response = {"uhid_number":PaymentUtils.get_uhid_number(payment_instance)}
            drive_booking = DriveBooking.objects.get(payment__id=payment_instance.id)
            payment_response = PaymentUtils.process_prepayment_uhid_registration_for_drive_booking(payment_instance,drive_booking,order_details,order_payment_details,payment_response)
            PaymentUtils.update_drive_booking_payment_details_with_manipal(payment_instance,order_details,order_payment_details,drive_booking)
            return payment_response

    @staticmethod
    def process_prepayment_uhid_registration_for_drive_booking(payment_instance,drive_booking,order_details,order_payment_details,payment_response):
        if payment_instance.payment_for_uhid_creation:
            registration_amount = PaymentUtils.get_registration_charges(drive_booking)
            pay_mode = None
            if not registration_amount:
                pay_mode=PaymentConstants.DRIVE_BOOKING_PAY_MODE_FOR_UHID
            payment_response = PaymentUtils.update_uhid_payment_details_with_manipal(payment_instance,order_details,order_payment_details,pay_mode=pay_mode,amount=registration_amount)
            PaymentUtils.payment_for_uhid_creation_method(payment_instance,payment_response)
        return payment_response
        
    @staticmethod
    def get_successful_payment_response(payment_instance):
        response_data = dict()
        if payment_instance.payment_for_uhid_creation and not payment_instance.appointment and not payment_instance.payment_for_health_package and not payment_instance.payment_for_drive:
            response_data.update({
                "uhid_number":PaymentUtils.get_uhid_number(payment_instance),
                "ReceiptNo": payment_instance.receipt_number
            })
        elif payment_instance.appointment or payment_instance.payment_for_health_package:
            response_data.update({
                "uhid_number":PaymentUtils.get_uhid_number(payment_instance),
                "ReceiptNo": payment_instance.receipt_number,
                "appointment_identifier":PaymentUtils.get_appointment_identifier(payment_instance),
                "StatusMessage": payment_instance.status
            })
        elif payment_instance.payment_for_op_billing:
            response_data.update({
                "uhid_number":PaymentUtils.get_uhid_number(payment_instance),
                "ReceiptNo": payment_instance.receipt_number,
                "EpisodeNo":payment_instance.episode_number,
                "StatusMessage": payment_instance.status
            })
        elif payment_instance.payment_for_ip_deposit or payment_instance.payment_for_drive:
            response_data.update({
                "uhid_number":PaymentUtils.get_uhid_number(payment_instance),
                "ReceiptNo": payment_instance.receipt_number,
                "StatusMessage": payment_instance.status
            })
        return response_data
