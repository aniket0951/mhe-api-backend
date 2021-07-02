

import logging
from time import sleep

from apps.appointments.models import Appointment
from apps.appointments.serializers import (HealthPackageAppointmentDetailSerializer,)
from apps.appointments.utils import cancel_and_refund_parameters

from proxy.custom_serializers import ObjectSerializer as custom_serializer
from proxy.custom_serializables import EpisodeItems as serializable_EpisodeItems
from proxy.custom_serializables import IPBills as serializable_IPBills
from proxy.custom_serializables import OPBills as serializable_OPBills
from proxy.custom_serializables import CorporateRegistration as serializable_CorporateRegistration
from proxy.custom_views import ProxyView

from rest_framework import filters, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.test import APIClient
from rest_framework.views import APIView
from rest_framework.exceptions import APIException
from utils import custom_viewsets

from utils.custom_permissions import (InternalAPICall, IsManipalAdminUser, IsPatientUser, IsSelfUserOrFamilyMember)
from utils.custom_sms import send_sms
from utils.razorpay_payment_parameter_generator import get_payment_param_for_razorpay
from utils.razorpay_refund_parameter_generator import get_refund_param_for_razorpay

from .exceptions import ProcessingIdDoesNotExistsValidationException,IncompletePaymentCannotProcessRefund, UnsuccessfulPaymentException
from .models import Payment, PaymentReceipts
from .serializers import (PaymentReceiptsSerializer, PaymentSerializer)
from .utils import PaymentUtils

from apps.payments.constants import PaymentConstants
from apps.payments.views import RefundView
from apps.additional_features.serializers import DriveBookingSerializer

logger = logging.getLogger('django')
client = APIClient()


class RazorAppointmentPayment(APIView):
    permission_classes = (IsPatientUser,)

    def post(self, request, format=None):
        
        param = get_payment_param_for_razorpay(request.data)

        location_code = request.data.get("location_code", None)
        appointment = request.data.get("appointment_id")
        registration_payment = request.data.get("registration_payment", False)

        hospital = PaymentUtils.get_hospital_from_location_code(location_code)
        appointment_instance = PaymentUtils.get_appointment_instance(appointment)
        param = PaymentUtils.set_param_for_appointment(param,appointment)
        payment_data = PaymentUtils.set_payment_data_for_appointment(request,param,appointment_instance,hospital)
        
        if registration_payment:
            payment_data["payment_for_uhid_creation"] = True

        PaymentUtils.validate_order_amount_for_appointments(request,appointment_instance,location_code,param)
        
        param,payment_data = PaymentUtils.set_order_id_for_appointments(param,payment_data)

        payment = PaymentSerializer(data=payment_data)
        payment.is_valid(raise_exception=True)
        payment.save()

        return Response(data=param, status=status.HTTP_200_OK)


class RazorHealthPackagePayment(APIView):
    permission_classes = (IsPatientUser,)

    def post(self, request, format=None):

        param = get_payment_param_for_razorpay(request.data)

        location_code = request.data.get("location_code", None)
        appointment = request.data.get("appointment_id", None)
        
        hospital = PaymentUtils.get_hospital_from_location_code(location_code)
        appointment_instance = PaymentUtils.get_health_package_appointment(appointment)
        package_code,package_code_list = PaymentUtils.get_health_package_code(request)
        param = PaymentUtils.set_param_for_health_package(param,package_code,appointment)
        payment_data = PaymentUtils.set_payment_data_for_health_package(request,param,hospital,appointment_instance)

        PaymentUtils.validate_order_amount_for_health_package(param,location_code,package_code_list)

        param,payment_data = PaymentUtils.set_order_id_for_health_package(param,payment_data)

        payment = PaymentSerializer(data=payment_data)
        payment.is_valid(raise_exception=True)
        payment.save()
        return Response(data=param, status=status.HTTP_200_OK)


class RazorUHIDPayment(APIView):
    permission_classes = (IsPatientUser,)

    def post(self, request, format=None):
        
        location_code = request.data.get("location_code", None)

        hospital = PaymentUtils.get_hospital_from_location_code(location_code)
        param = get_payment_param_for_razorpay(request.data)
        param = PaymentUtils.set_param_for_uhid(param,location_code)
        payment_data = PaymentUtils.set_payment_data_for_uhid(request,param,hospital)

        PaymentUtils.validate_order_amount_for_uhid(param,location_code)

        param,payment_data = PaymentUtils.set_order_id_for_uhid(param,payment_data)

        payment_data["payment_for_uhid_creation"] = True

        payment = PaymentSerializer(data=payment_data)
        payment.is_valid(raise_exception=True)
        payment.save()
        return Response(data=param, status=status.HTTP_200_OK)


class RazorOPBillPayment(APIView):
    permission_classes = (IsPatientUser,)

    def post(self, request, format=None):
        
        location_code = request.data.get("location_code", None)
        episode_no = request.data.get("episode_no", None)
        bill_row_id = request.data.get("bill_row_id", None)

        hospital = PaymentUtils.get_hospital_from_location_code(location_code)
        param = get_payment_param_for_razorpay(request.data)
        param = PaymentUtils.set_param_for_op_bill(param,location_code,episode_no,bill_row_id)
        payment_data = PaymentUtils.set_payment_data_for_op_bill(request,param,hospital,episode_no,bill_row_id)

        PaymentUtils.validate_order_amount_for_op_bill(param,location_code,episode_no,bill_row_id)

        param,payment_data = PaymentUtils.set_order_id_for_op_bill(param,payment_data)

        payment = PaymentSerializer(data=payment_data)
        payment.is_valid(raise_exception=True)
        payment.save()
        return Response(data=param, status=status.HTTP_200_OK)


class RazorIPDepositPayment(APIView):
    permission_classes = (IsPatientUser,)

    def post(self, request, format=None):
        location_code = request.data.get("location_code", None)
        hospital = PaymentUtils.get_hospital_from_location_code(location_code)
        param = get_payment_param_for_razorpay(request.data)
        param = PaymentUtils.set_param_for_ip_deposit(param,location_code)
        payment_data = PaymentUtils.set_payment_data_for_ip_deposit(request,param,hospital)
        param,payment_data = PaymentUtils.set_order_id_for_ip_deposit(param,payment_data)
        payment = PaymentSerializer(data=payment_data)
        payment.is_valid(raise_exception=True)
        payment.save()
        return Response(data=param, status=status.HTTP_200_OK)


class RazorDrivePayment(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        param = get_payment_param_for_razorpay(request.data)

        location_code = request.data.get("location_code", None)
        drive_booking = request.data.get("drive_booking_id")
        
        registration_payment = request.data.get("registration_payment", False)

        hospital = PaymentUtils.get_hospital_from_location_code(location_code)
        drive_booking_instance = PaymentUtils.get_drive_booking_instance(drive_booking)
        
        param = PaymentUtils.set_param_for_drive_booking(param,drive_booking_instance.drive.id)
        payment_data = PaymentUtils.set_payment_data_for_drive_booking(request,param,drive_booking_instance,hospital)
        
        if registration_payment:
            payment_data["payment_for_uhid_creation"] = True

        PaymentUtils.validate_order_amount_for_drive_booking(request,drive_booking_instance,location_code,param)
        
        param['is_completed'] = False
        if int(float(param["token"]["accounts"][0]["amount"])) == 0:
            param['is_completed'] = True
            payment_data['status'] = PaymentConstants.MANIPAL_PAYMENT_STATUS_SUCCESS
        else:
            param,payment_data = PaymentUtils.set_order_id_for_drive_booking(param,payment_data)

        payment = PaymentSerializer(data=payment_data)
        payment.is_valid(raise_exception=True)
        payment_id = payment.save()

        drive_booking_serializer = DriveBookingSerializer(drive_booking_instance.id,data={'payment':payment_id.id}, partial=True)
        drive_booking_serializer.is_valid(raise_exception=True)
        drive_booking = drive_booking_serializer.save()

        return Response(data=param, status=status.HTTP_200_OK)


class RazorPaymentResponse(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):

        logger.info("Payment Request data: %s"%str(request.data))

        is_requested_from_mobile = False
        if request.data.get("order_id") and request.data.get("processing_id"):
            is_requested_from_mobile = True
        
        payment_instance = PaymentUtils.validate_and_wait_for_mobile_request(request,is_requested_from_mobile)

        if payment_instance.status in [PaymentConstants.MANIPAL_PAYMENT_STATUS_SUCCESS,PaymentConstants.MANIPAL_PAYMENT_STATUS_REFUNDED]:
            return Response(data=PaymentUtils.get_successful_payment_response(payment_instance), status=status.HTTP_200_OK)

        order_details = PaymentUtils.get_razorpay_order_details_payment_instance(payment_instance)
        order_payment_details = PaymentUtils.get_razorpay_order_payment_response(request,order_details,payment_instance)
        PaymentUtils.validate_order_details_status(order_details,order_payment_details,payment_instance)

        if order_payment_details.get("status") in [PaymentConstants.RAZORPAY_PAYMENT_STATUS_FAILED]:
            return Response(data=PaymentUtils.get_successful_payment_response(payment_instance), status=status.HTTP_200_OK)

        payment_response = dict()
        try:
            
            payment_response = PaymentUtils.update_manipal_on_payment(is_requested_from_mobile,payment_instance,order_details,order_payment_details)
            PaymentUtils.update_payment_details(payment_instance,payment_response,order_details,order_payment_details,is_requested_from_mobile)
            PaymentUtils.payment_for_uhid_creation(payment_instance,payment_response)
            PaymentUtils.payment_for_scheduling_appointment(payment_instance,payment_response,order_details)
            PaymentUtils.payment_update_for_health_package(payment_instance,payment_response)
            PaymentUtils.payment_update_for_drive_booking(payment_instance)

        except Exception as e:
            logger.error("Error while processing payment : %s"%str(e))
            PaymentUtils.update_failed_payment_response(payment_instance,order_details,order_payment_details,is_requested_from_mobile)
            
        return Response(data=PaymentUtils.get_successful_payment_response(payment_instance), status=status.HTTP_200_OK)

class RazorRefundView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):

        appointment_identifier = request.data.get("appointment_identifier", None)
        appointment_instance = Appointment.objects.filter(appointment_identifier=appointment_identifier).first()

        if appointment_instance.payment_appointment.exists():
            param = get_refund_param_for_razorpay(request.data)
            payment_instance = appointment_instance.payment_appointment.filter(status=PaymentConstants.MANIPAL_PAYMENT_STATUS_SUCCESS).first()
            
            if not payment_instance:
                raise IncompletePaymentCannotProcessRefund
            razor_payment_id = None
            if payment_instance.razor_payment_id:
                razor_payment_id = payment_instance.razor_payment_id
            elif payment_instance.razor_order_id:
                razor_payment_data = PaymentUtils.get_razorpay_payment_data_from_order_id(param.get("key"),param.get("secret"),payment_instance.razor_order_id)
                razor_payment_id = razor_payment_data.get("id")
            else:
                refund_param = cancel_and_refund_parameters({"appointment_identifier": appointment_identifier})
                RefundView.as_view()(refund_param)
                return Response(status=status.HTTP_200_OK)
            
            if not razor_payment_id:
                raise IncompletePaymentCannotProcessRefund

            refunded_payment_details = dict()

            if param.get("amount") and int(param.get("amount"))>0:
                refunded_payment_details = PaymentUtils.initiate_refund(
                                            hospital_key=param.get("key"),
                                            hospital_secret=param.get("secret"),
                                            payment_id=razor_payment_id,
                                            amount_to_be_refunded=int(param.get("amount"))
                                        )
            if refunded_payment_details:
                amount = param.get("amount")
                PaymentUtils.update_refund_payment_response(refunded_payment_details,payment_instance,amount)

                appointment_instance.payment_status = PaymentConstants.MANIPAL_PAYMENT_STATUS_REFUNDED
                appointment_instance.save()

                payment_instance.status = PaymentConstants.MANIPAL_PAYMENT_STATUS_REFUNDED
                payment_instance.save()

        return Response(status=status.HTTP_200_OK)
