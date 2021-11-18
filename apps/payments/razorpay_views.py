import logging

from apps.patients.models import FamilyMember, Patient
from apps.appointments.models import Appointment
from apps.appointments.serializers import (HealthPackageAppointmentDetailSerializer,)
from apps.appointments.utils import cancel_and_refund_parameters

from rest_framework import filters,status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.test import APIClient
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from utils.custom_permissions import (IsPatientUser,IsManipalAdminUser)
from utils import custom_viewsets

from utils.razorpay_payment_parameter_generator import get_payment_param_for_razorpay
from utils.razorpay_refund_parameter_generator import get_refund_param_for_razorpay

from .exceptions import IncompletePaymentCannotProcessRefund, PaymentProcessingFailedRefundProcessedException, UnsuccessfulPaymentException
from .models import Payment, PaymentReceipts, UnprocessedTransactions
from .serializers import (PaymentReceiptsSerializer, PaymentSerializer, UnprocessedTransactionsSerializer)
from .utils import PaymentUtils
from apps.additional_features.models import DriveBooking

from apps.payments.constants import PaymentConstants
from apps.payments.views import RefundView
from apps.additional_features.serializers import DriveBookingSerializer
from apps.patients.models import Patient,FamilyMember

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
        
        if appointment_instance.family_member:
            user = appointment_instance.family_member
        else:
            user = Patient.objects.filter(id=request.user.id).first()
        
        param,payment_data = PaymentUtils.set_order_id_for_appointments(param,payment_data,user)

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

        if appointment_instance.family_member:
            user = appointment_instance.family_member
        else:
            user = Patient.objects.filter(id=request.user.id).first()

        param,payment_data = PaymentUtils.set_order_id_for_health_package(param,payment_data,user)

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

        if request.data.get("user_id", None):
            user = FamilyMember.objects.filter(id=request.data.get("user_id", None)).first()
        else:
            user = Patient.objects.filter(id=request.user.id).first()

        param,payment_data = PaymentUtils.set_order_id_for_uhid(param,payment_data,user)

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

        if request.data.get("user_id", None):
            user = FamilyMember.objects.filter(id=request.data.get("user_id", None)).first()
        else:
            user = Patient.objects.filter(id=request.user.id).first()

        param,payment_data = PaymentUtils.set_order_id_for_op_bill(param,payment_data,user)

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

        if request.data.get("user_id", None):
            user = FamilyMember.objects.filter(id=request.data.get("user_id", None)).first()
        else:
            user = Patient.objects.filter(id=request.user.id).first()

        param,payment_data = PaymentUtils.set_order_id_for_ip_deposit(param,payment_data,user)
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
        
        drive_update_data = {}
        param['is_completed'] = False

        if int(float(param["token"]["accounts"][0]["amount"])) == 0:
            param['is_completed'] = True
            payment_data['status'] = PaymentConstants.MANIPAL_PAYMENT_STATUS_SUCCESS
            payment_data['amount'] = 0
            payment_data['transaction_id'] = param["token"]["processing_id"]
            drive_update_data.update({'status':DriveBooking.BOOKING_BOOKED})
            
        else:

            if request.data.get("user_id", None):
                user = FamilyMember.objects.filter(id=request.data.get("user_id", None)).first()
            else:
                user = Patient.objects.filter(id=request.user.id).first()

            param,payment_data = PaymentUtils.set_order_id_for_drive_booking(param,payment_data,user)

        payment = PaymentSerializer(data=payment_data)
        payment.is_valid(raise_exception=True)
        payment_id = payment.save()

        drive_update_data.update({'payment':payment_id.id})

        drive_booking_serializer = DriveBookingSerializer(drive_booking_instance,data=drive_update_data, partial=True)
        drive_booking_serializer.is_valid(raise_exception=True)
        drive_booking = drive_booking_serializer.save()

        if int(float(param["token"]["accounts"][0]["amount"])) == 0:
            if payment_data.get("payment_for_uhid_creation"):
                order_details = {"id":param["token"]["processing_id"]}
                try:
                    payment_response = PaymentUtils.update_uhid_payment_details_with_manipal(
                                                            payment_id,
                                                            order_details,
                                                            order_details,
                                                            pay_mode=PaymentConstants.DRIVE_BOOKING_PAY_MODE_FOR_UHID,
                                                            amount=0
                                                        )
                    PaymentUtils.payment_for_uhid_creation_method(payment_id,payment_response)
                    payment = PaymentSerializer(payment_id,data=payment_response,partial=True)
                    payment.is_valid(raise_exception=True)
                    payment.save()
                except Exception as e:
                    logger.error("Error while processing payment : %s"%str(e))
                    PaymentUtils.cancel_drive_booking_on_failure(payment_id)
                    payment = PaymentSerializer(payment_id,data={"status":PaymentConstants.MANIPAL_PAYMENT_STATUS_FAILED},partial=True)
                    payment.is_valid(raise_exception=True)
                    payment.save()
                    raise ValidationError("UHID Creation failed!")
                
            param['is_completed'] = True
            payment_data['status'] = PaymentConstants.MANIPAL_PAYMENT_STATUS_SUCCESS
            payment_data['amount'] = 0
            payment_data['transaction_id'] = param["token"]["processing_id"]
            drive_update_data.update({'status':DriveBooking.BOOKING_BOOKED})

        return Response(data=param, status=status.HTTP_200_OK)


class RazorPaymentResponse(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):

        logger.info("Payment Request data: %s"%str(request.data))

        is_requested_from_mobile = False
        if request.data.get("order_id") and request.data.get("processing_id"):
            is_requested_from_mobile = True

        is_request_from_cron = False
        if request.data.get("cron"):
            is_request_from_cron = True
        
        payment_instance = PaymentUtils.validate_and_wait_for_mobile_request(request,is_requested_from_mobile)

        if not is_request_from_cron and payment_instance.status in [PaymentConstants.MANIPAL_PAYMENT_STATUS_SUCCESS,PaymentConstants.MANIPAL_PAYMENT_STATUS_REFUNDED]:
            return Response(data=PaymentUtils.get_successful_payment_response(payment_instance), status=status.HTTP_200_OK)

        order_details = PaymentUtils.get_razorpay_order_details_payment_instance(payment_instance)
        order_payment_details = PaymentUtils.get_razorpay_order_payment_response(request,order_details,payment_instance)
        PaymentUtils.validate_order_details_status(order_details,order_payment_details,payment_instance)

        
        logger.info("Payment Request order_payment_details: %s"%str(order_payment_details))

        if not is_request_from_cron and order_payment_details.get("status") in [PaymentConstants.RAZORPAY_PAYMENT_STATUS_FAILED]:
            return Response(data=PaymentUtils.get_successful_payment_response(payment_instance), status=status.HTTP_200_OK)

        payment_response = dict()
        try:
            
            payment_response = PaymentUtils.update_manipal_on_payment(is_requested_from_mobile,payment_instance,order_details,order_payment_details)
            PaymentUtils.update_payment_details(payment_instance,payment_response,order_details,order_payment_details,is_requested_from_mobile)
            PaymentUtils.payment_for_uhid_creation_method(payment_instance,payment_response)
            PaymentUtils.payment_for_scheduling_appointment(payment_instance,payment_response,order_details,is_requested_from_mobile)
            PaymentUtils.payment_update_for_health_package(payment_instance,payment_response)
            PaymentUtils.payment_update_for_drive_booking(payment_instance)

        except Exception as e:
            if is_request_from_cron:
                raise PaymentProcessingFailedRefundProcessedException
                
            logger.error("Error while processing payment : %s"%str(e))
            PaymentUtils.cancel_drive_booking_on_failure(payment_instance)
            PaymentUtils.update_failed_payment_response_with_refund(payment_instance,order_details,order_payment_details,is_requested_from_mobile)
            PaymentUtils.update_failed_payment_response_without_refund(payment_instance,order_details,order_payment_details,is_requested_from_mobile)
            
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


class UnprocessedTransactionsViewSet(custom_viewsets.CreateUpdateListRetrieveModelViewSet):
    queryset = UnprocessedTransactions.objects.all()
    serializer_class = UnprocessedTransactionsSerializer
    permission_classes = [IsManipalAdminUser]
    list_success_message = 'Unprocessed Transactions returned successfully!'
    retrieve_success_message = 'Unprocessed Transaction returned successfully!'
    filter_backends = (
                DjangoFilterBackend,
                filters.SearchFilter, 
                filters.OrderingFilter
            )
    search_fields = [
            'payment__razor_order_id',
            'payment__razor_payment_id',
            'payment__uhid_number',
            'health_package_appointment__appointment_identifier'
        ]
    
class InitiateManualRefundAPI(APIView):
    permission_classes = (IsManipalAdminUser,)

    def post(self, request, format=None):

        logger.info("Payment Request data: %s"%str(request.data))

        is_requested_from_mobile = False
     
        payment_instance = PaymentUtils.validate_and_wait_for_mobile_request(request,is_requested_from_mobile)
        order_details = PaymentUtils.get_razorpay_order_details_payment_instance(payment_instance)
        order_payment_details = PaymentUtils.get_razorpay_order_payment_response(request,order_details,payment_instance)
        PaymentUtils.validate_order_details_status(order_details,order_payment_details,payment_instance)
                
        PaymentUtils.cancel_drive_booking_on_failure(payment_instance)
        PaymentUtils.update_failed_payment_response(payment_instance,order_details,order_payment_details,is_requested_from_mobile)
