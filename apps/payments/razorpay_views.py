from apps.payments.constants import PaymentConstants
import base64
import hashlib
import json
import logging
from utils.razorpay_util import RazorPayUtil
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from random import randint

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render

from apps.appointments.models import Appointment, HealthPackageAppointment
from apps.appointments.serializers import (HealthPackageAppointmentDetailSerializer,)
from apps.manipal_admin.models import ManipalAdmin
from apps.patients.models import Patient
from django_filters.rest_framework import DjangoFilterBackend
from proxy.custom_serializables import EpisodeItems as serializable_EpisodeItems
from proxy.custom_serializables import IPBills as serializable_IPBills
from proxy.custom_serializables import OPBills as serializable_OPBills
from proxy.custom_serializables import CorporateRegistration as serializable_CorporateRegistration
from proxy.custom_serializers import ObjectSerializer as custom_serializer
from proxy.custom_views import ProxyView
from rest_framework import filters, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.test import APIClient
from rest_framework.views import APIView
from utils import custom_viewsets
from utils.custom_permissions import (IsManipalAdminUser, IsPatientUser,
                                      IsSelfUserOrFamilyMember)
from utils.custom_sms import send_sms
from utils.razorpay_payment_parameter_generator import get_payment_param_for_razorpay
from utils.razorpay_refund_parameter_generator import get_refund_param_for_razorpay

from .exceptions import ProcessingIdDoesNotExistsValidationException
from .models import Payment, PaymentReceipts, PaymentRefund
from .serializers import (PaymentReceiptsSerializer, PaymentRefundSerializer,
                          PaymentSerializer)

from .utils import PaymentUtils

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

        logger.info(param)

        return Response(data=param, status=status.HTTP_200_OK)


class RazorHealthPackagePayment(APIView):
    permission_classes = (IsPatientUser,)

    def post(self, request, format=None):

        param = get_payment_param_for_razorpay(request.data)

        location_code = request.data.get("location_code", None)
        registration_payment = request.data.get("registration_payment", False)
        appointment = request.data.get("appointment_id", None)
        family_member = request.data.get("user_id", None)

        hospital = PaymentUtils.get_hospital_from_location_code(location_code)
        appointment_instance = PaymentUtils.get_appointment_instance(appointment)
        package_code,package_code_list = PaymentUtils.get_health_package_code(request)
        param = PaymentUtils.set_param_for_health_package(param,package_code,appointment)
        payment_data = PaymentUtils.set_payment_data_for_health_package(request,param,hospital,appointment_instance,registration_payment,family_member)

        PaymentUtils.validate_order_amount_for_health_package(param,location_code,package_code_list)

        param,payment_data = PaymentUtils.set_order_id_for_health_package(param,payment_data)

        payment = PaymentSerializer(data=payment_data)
        payment.is_valid(raise_exception=True)
        payment.save()
        logger.info(param)
        return Response(data=param, status=status.HTTP_200_OK)


class RazorUHIDPayment(APIView):
    permission_classes = (IsPatientUser,)

    def post(self, request, format=None):
        
        family_member = request.data.get("user_id", None)
        location_code = request.data.get("location_code", None)

        hospital = PaymentUtils.get_hospital_from_location_code(location_code)
        param = get_payment_param_for_razorpay(request.data)
        param = PaymentUtils.set_param_for_uhid(param,location_code)
        payment_data = PaymentUtils.set_payment_data_for_uhid(request,param,hospital,family_member)

        PaymentUtils.validate_order_amount_for_uhid(param,location_code)

        param,payment_data = PaymentUtils.set_order_id_for_uhid(param,payment_data)

        payment_data["payment_for_uhid_creation"] = True

        payment = PaymentSerializer(data=payment_data)
        payment.is_valid(raise_exception=True)
        payment.save()
        logger.info(param)

        return Response(data=param, status=status.HTTP_200_OK)


class RazorOPBillPayment(APIView):
    permission_classes = (IsPatientUser,)

    def post(self, request, format=None):
        
        family_member = request.data.get("user_id", None)
        location_code = request.data.get("location_code", None)
        episode_no = request.data.get("episode_no", None)

        hospital = PaymentUtils.get_hospital_from_location_code(location_code)
        param = get_payment_param_for_razorpay(request.data)
        param = PaymentUtils.set_param_for_op_bill(param,location_code,episode_no)
        payment_data = PaymentUtils.set_payment_data_for_op_bill(request,param,hospital,family_member,episode_no)

        PaymentUtils.validate_order_amount_for_op_bill()

        param,payment_data = PaymentUtils.set_order_id_for_op_bill(param,payment_data)

        payment = PaymentSerializer(data=payment_data)
        payment.is_valid(raise_exception=True)
        payment.save()
        logger.info(param)
        return Response(data=param, status=status.HTTP_200_OK)


class RazorIPDepositPayment(APIView):
    permission_classes = (IsPatientUser,)

    def post(self, request, format=None):
        family_member = request.data.get("user_id", None)
        location_code = request.data.get("location_code", None)
        hospital = PaymentUtils.get_hospital_from_location_code(location_code)
        param = get_payment_param_for_razorpay(request.data)
        param = PaymentUtils.set_param_for_ip_deposit(param,location_code)
        payment_data = PaymentUtils.set_payment_data_for_ip_deposit(request,param,hospital,family_member)
        payment = PaymentSerializer(data=payment_data)
        payment.is_valid(raise_exception=True)
        payment.save()
        logger.info(param)
        return Response(data=param, status=status.HTTP_200_OK)

class RazorPaymentResponse(APIView):
    permission_classes = (IsPatientUser,)

    def post(self, request, format=None):

        processing_id = request.data.get("processing_id")
        razor_order_id = request.data.get("order_id")
        payment_instance = PaymentUtils.get_payment_instance(processing_id,razor_order_id)
        order_details = PaymentUtils.get_razorpay_order_details_payment_instance(payment_instance,razor_order_id)
        order_payment_details = PaymentUtils.get_razorpay_fetch_order_payments_payment_instance(order_details,payment_instance,razor_order_id)
        payment_instance.raw_info_from_salucro_response = order_details
        payment_instance.save()
        payment_response = {}
        if order_details.get("status")==PaymentConstants.RAZORPAY_PAYMENT_STATUS_PAID:
            payment_response = PaymentUtils.update_manipal_on_payment(payment_instance,razor_order_id)
            PaymentUtils.update_payment_details(payment_instance,payment_response,order_details,order_payment_details)
            PaymentUtils.payment_for_uhid_creation(payment_instance,payment_response)
            PaymentUtils.payment_for_scheduling_appointment(payment_instance,payment_response)
            PaymentUtils.payment_for_health_package(payment_instance,payment_response)
        else:
            payment_instance.status = order_details.get("status")
            payment_instance.save()
        return Response(data=payment_response, status=status.HTTP_200_OK)
      
class OldRazorPaymentResponse(APIView):
    permission_classes = (IsPatientUser,)

    def post(self, request, format=None):

        processing_id = request.data.get("processing_id")
        razor_order_id = request.data.get("order_id")
        payment_instance = PaymentUtils.get_payment_instance(processing_id,razor_order_id)
        order_details = PaymentUtils.get_razorpay_order_details_payment_instance(payment_instance,razor_order_id)
        
        uhid = "-1"
        payment_instance.raw_info_from_salucro_response = order_details
        payment_instance.save()

        response_token = request.data["responseToken"]
        response_token_json = json.loads(response_token)
        status_code = response_token_json["status_code"]
        payment_response = response_token_json["payment_response"]
        payment_account = response_token_json["accounts"]
        
        if status_code == 1200:
            payment = PaymentUtils.initialize_payment_details(payment_account)
            payment = PaymentUtils.set_payment_details_for_appointment_health_package(payment_instance,payment_response,payment)
            payment = PaymentUtils.set_payment_details_for_uhid_with_appointment_health_package(payment_instance,payment_response,payment)
            payment = PaymentUtils.set_payment_details_for_op_billing(payment_instance,payment_response,payment)
            payment = PaymentUtils.set_payment_details_for_ip_deposit(payment_instance,payment_response,payment)
            PaymentUtils.update_payment_details(payment_instance,payment_response,payment)
        
            uhid_info = PaymentUtils.initialize_uhid_info(payment)
            if uhid_info.get("uhid_number"):
                uhid = uhid_info.get("uhid_number")
            PaymentUtils.payment_for_uhid_creation(payment_instance,uhid_info)
            PaymentUtils.payment_for_scheduling_appointment(payment_instance,payment_response,payment)
            PaymentUtils.payment_for_health_package(payment_instance,payment_response)
        else:
            payment_instance.status = "failure"
            payment_instance.uhid_number = payment_account["account_number"]
            payment_instance.save()
        txnstatus = response_token_json["status_code"]
        txnamount = payment_response["net_amount_debit"]
        txnid = payment_response["txnid"]
        param = "?txnid={0}&txnstatus={1}&txnamount={2}&uhidNumber={3}".format(
            txnid, txnstatus, txnamount, uhid)
            
        return HttpResponseRedirect(settings.REDIRECT_URL + param)

class RazorPaymentReturn(APIView):
    permission_classes = (AllowAny,)
    parser_classes = [FormParser, MultiPartParser, JSONParser]

    def post(self, request, format=None):
        data = request.data
        response_token = data["responseToken"]
        response_token_json = json.loads(response_token)
        processing_id = response_token_json["processing_id"]
        try:
            payment_instance = Payment.objects.get(processing_id=processing_id)
        except Exception:
            raise ProcessingIdDoesNotExistsValidationException
        payment_response = response_token_json["payment_response"]
        payment_account = response_token_json["accounts"]
        txnstatus = response_token_json["status_code"]
        txnamount = payment_response["net_amount_debit"]
        txnid = payment_response["txnid"]
        uhid = payment_instance.uhid_number
        if not uhid:
            uhid = "-1"

        param = "?txnid={0}&txnstatus={1}&txnamount={2}&uhidNumber={3}".format(
            txnid, txnstatus, txnamount, uhid)
        return HttpResponseRedirect(settings.REDIRECT_URL + param)


class RazorPaymentsAPIView(custom_viewsets.ReadOnlyModelViewSet):
    search_fields = ['patient__first_name']
    filter_backends = (filters.SearchFilter,
                       filters.OrderingFilter, DjangoFilterBackend)
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    ordering = ('-created_at',)
    filter_fields = ('status',)
    permission_classes = [IsManipalAdminUser | IsSelfUserOrFamilyMember]
    list_success_message = 'Payment list returned successfully!'
    retrieve_success_message = 'Payment information returned successfully!'

    def get_queryset(self):
        uhid = self.request.query_params.get("uhid", None)
        filter_by = self.request.query_params.get("filter_by", None)
        if ManipalAdmin.objects.filter(id=self.request.user.id).exists():
            return super().get_queryset()
        if filter_by:
            if filter_by == "current_week":
                current_week = date.today().isocalendar()[1]
                current_year = date.today().isocalendar()[0]
                return super().get_queryset().filter(uhid_number=uhid, created_at__week=current_week, created_at__year=current_year)
            elif filter_by == "last_week":
                previous_week = date.today() - timedelta(weeks=1)
                last_week = previous_week.isocalendar()[1]
                current_year = previous_week.isocalendar()[0]
                return super().get_queryset().filter(uhid_number=uhid, created_at__week=last_week, created_at__year=current_year)
            elif filter_by == "last_month":
                last_month = datetime.today().replace(day=1) - timedelta(days=1)
                return super().get_queryset().filter(uhid_number=uhid, created_at__month=last_month.month, created_at__year=last_month.year)
            elif filter_by == "current_month":
                current_month = datetime.today()
                return super().get_queryset().filter(uhid_number=uhid, created_at__month=current_month.month, created_at__year=current_month.year)
            elif filter_by == "date_range":
                date_from = self.request.query_params.get("date_from", None)
                date_to = self.request.query_params.get("date_to", None)
                return super().get_queryset().filter(uhid_number=uhid, created_at__date__range=[date_from, date_to])
            else:
                return super().get_queryset().filter(uhid_number=uhid, created_at__date=filter_by)
        return super().get_queryset().filter(uhid_number=uhid)


class RazorHealthPackageAPIView(custom_viewsets.ReadOnlyModelViewSet):
    search_fields = ['payment_id__payment_done_for_patient__first_name', 'payment_id__payment_done_for_family_member__first_name',
                     'payment_id__uhid_number', 'payment_id__payment_done_for_patient__mobile',
                     'payment_id__payment_done_for_family_member__mobile', 'payment_id__location__description',
                     'health_package__code', 'health_package__name']
    filter_backends = (filters.SearchFilter,
                       filters.OrderingFilter, DjangoFilterBackend)
    queryset = HealthPackageAppointment.objects.all()
    ordering = ('-payment_id__created_at',)
    filter_fields = ('appointment_status', 'payment_id__status')
    ordering_fields = ('appointment_date',)
    serializer_class = HealthPackageAppointmentDetailSerializer
    permission_classes = [IsManipalAdminUser | IsSelfUserOrFamilyMember]
    list_success_message = 'Health Package list returned successfully!'

    def get_queryset(self):
        qs = super().get_queryset()
        uhid = self.request.query_params.get("uhid", None)
        is_booked = self.request.query_params.get("is_booked", None)
        if ManipalAdmin.objects.filter(id=self.request.user.id).exists():
            date_from = self.request.query_params.get("date_from", None)
            date_to = self.request.query_params.get("date_to", None)
            if date_from and date_to:
                qs = qs.filter(payment_id__status="success",
                               appointment_date__date__range=[date_from, date_to])
            return qs.filter(payment_id__status="success")
        if is_booked:
            return qs.filter(payment_id__uhid_number=uhid, payment_id__uhid_number__isnull=False, payment_id__status="success", appointment_status="Booked")
        return qs.filter(payment_id__uhid_number=uhid, payment_id__uhid_number__isnull=False, payment_id__status="success").filter(Q(appointment_status="Booked") | Q(appointment_status="Cancelled"))


class RazorPayBillView(ProxyView):
    source = 'DepositAmt'
    permission_classes = [IsSelfUserOrFamilyMember]

    def get_request_data(self, request):
        pay_bill = serializable_IPBills(**request.data)
        request_data = custom_serializer().serialize(pay_bill, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response.content)
        response_data = {}
        response_message = "We are unable to cancel fetch the bill information. Please Try again"
        success_status = False
        if response.status_code == 200:
            status = root.find("Status").text
            if status == "1":
                success_status = True
                response_message = "Returned Bill Information Successfully"
                bill_response = root.find("BillDetail")
                response_data = json.loads(bill_response.text)

        return self.custom_success_response(message=response_message,
                                            success=success_status, data=response_data)


class RazorPayBillOpView(ProxyView):
    source = 'PatOutStandAmt'
    permission_classes = [IsSelfUserOrFamilyMember]

    def get_request_data(self, request):
        pay_bill = serializable_OPBills(**request.data)
        request_data = custom_serializer().serialize(pay_bill, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response.content)
        response_data = {}
        response_message = "We are unable to cancel fetch the bill information. Please Try again"
        success_status = False
        if response.status_code == 200:
            status = root.find("Status").text
            if status == "1":
                success_status = True
                response_message = "Returned Bill Information Successfully"
                bill_response = root.find("BillDetail")
                response_data = json.loads(bill_response.text)

        return self.custom_success_response(message=response_message,
                                            success=success_status, data=response_data)


class RazorEpisodeItemView(ProxyView):
    source = 'GetEpisodeItems'
    permission_classes = [IsSelfUserOrFamilyMember]

    def get_request_data(self, request):
        pay_bill = serializable_EpisodeItems(**request.data)
        request_data = custom_serializer().serialize(pay_bill, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response.content)
        response_data = {}
        response_message = "We are unable to fetch the Item information. Please Try again"
        success_status = False
        if response.status_code == 200:
            status = root.find("Status").text
            if status == "1":
                success_status = True
                response_message = "Returned Bill Information Successfully"
                episode_response = root.find("EpisodeList").text
                response_data = json.loads(episode_response)

        return self.custom_success_response(message=response_message,
                                            success=success_status, data=response_data)


class RazorRefundView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):

        appointment_identifier = request.data.get(
            "appointment_identifier", None)
        appointment_instance = Appointment.objects.filter(
            appointment_identifier=appointment_identifier).first()
        if appointment_instance.payment_appointment.exists():
            param = get_refund_param_for_razorpay(request.data)
            url = settings.REFUND_URL
            response = requests.post(url, data=param)
            data = json.loads(response.text)
            if data["status_code"] == 1200:
                payment_instance = appointment_instance.payment_appointment.filter(
                    status="success").first()
                if payment_instance:
                    refund_param = dict()
                    refund_param["payment"] = payment_instance.id
                    refund_param["uhid_number"] = data["accounts"]["account_number"]
                    refund_param["processing_id"] = data["processing_id"]
                    refund_param["transaction_id"] = data["transaction_id"]
                    if data["status_message"] == "Request processed successfully":
                        refund_param["status"] = "success"
                    refund_param["amount"] = data["accounts"]["amount"]
                    refund_param["receipt_number"] = data["payment_response"]["mihpayid"]
                    refund_param["request_id"] = data["payment_response"]["request_id"]
                    refund_instance = PaymentRefundSerializer(
                        data=refund_param)
                    refund_instance.is_valid(raise_exception=True)
                    refund_instance.save()
                    payment_instance.status = "Refunded"
                    appointment_instance.payment_status = "Refunded"
                    appointment_instance.save()
                    payment_instance.save()
        return Response(status=status.HTTP_200_OK)


class ReceiptViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [AllowAny, ]
    model = PaymentReceipts
    queryset = PaymentReceipts.objects.all().order_by('-created_at')
    serializer_class = PaymentReceiptsSerializer
    create_success_message = "Receipt is uploaded successfully."
    list_success_message = 'Receipts returned successfully!'
    retrieve_success_message = 'Receipts information returned successfully!'
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, )

    def get_queryset(self):
        queryset = super().get_queryset()
        uhid = self.request.query_params.get("uhid", None)
        if not uhid:
            raise ValidationError("Invalid Parameters")
        return queryset.filter(payment_info__uhid=uhid)

    def create(self, request):
        uhid = request.data.get("uhid", None)
        receipt_number = request.data.get("receipt_number", None)
        payment_data = dict()
        payment_instance = Payment.objects.filter(
            receipt_number=receipt_number).first()
        patient_instance = Patient.objects.filter(uhid_number=uhid).first()

        if not (payment_instance or patient_instance):
            raise ValidationError("Payment Instance or Patient does not Exist")

        payment_data["payment_info"] = payment_instance.id
        payment_data["patient_info"] = patient_instance.id
        payment_data["receipt_number"] = receipt_number

        file = request.FILES.getlist('receipt')[0]
        payment_data["receipt"] = file
        payment_data["name"] = file.name
        payment_data["receipt_date"] = datetime.strptime(
            request.data.get("receipt_date", None), '%Y%m%d%H%M%S')
        receipt_serializer = PaymentReceiptsSerializer(data=payment_data)
        receipt_serializer.is_valid(raise_exception=True)
        receipt_serializer.save()
        return Response(status=status.HTTP_200_OK)


class CorporateUhidRegistration(ProxyView):
    source = 'PaymentForRegistration'
    permission_classes = [AllowAny]

    def get_request_data(self, request):
        registration = serializable_CorporateRegistration(**request.data)
        request_data = custom_serializer().serialize(registration, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response.content)
        response_data = {}
        response_message = "We are unable to cancel fetch the information. Please Try again"
        success_status = False
        if response.status_code == 200:
            status = root.find("Status").text
            if status == "1":
                success_status = True
                response_message = "UHID Registration Successfully"
                uhid = root.find("UID").text
                patient = Patient.objects.filter(id=self.request.user.id).first()
                if patient:
                    patient.uhid_number = uhid
                    patient.save()
                response_data["uhid"] = uhid

        return self.custom_success_response(message=response_message,
                                            success=success_status, data=response_data)
