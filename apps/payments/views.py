import base64
import hashlib
import json
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
from apps.appointments.serializers import (
    AppointmentSerializer, HealthPackageAppointmentDetailSerializer,
    HealthPackageAppointmentSerializer)
from apps.health_packages.models import HealthPackage
from apps.health_packages.serializers import HealthPackageSerializer
from apps.manipal_admin.models import ManipalAdmin
from apps.master_data.exceptions import \
    HospitalDoesNotExistsValidationException
from apps.master_data.models import Hospital
from apps.patients.exceptions import PatientDoesNotExistsValidationException
from apps.patients.models import FamilyMember, Patient
from apps.patients.serializers import (FamilyMemberSpecificSerializer,
                                       PatientSpecificSerializer)
from django_filters.rest_framework import DjangoFilterBackend
from proxy.custom_serializables import \
    EpisodeItems as serializable_EpisodeItems
from proxy.custom_serializables import IPBills as serializable_IPBills
from proxy.custom_serializables import OPBills as serializable_OPBills
from proxy.custom_serializers import ObjectSerializer as custom_serializer
from proxy.custom_views import ProxyView
from rest_framework import filters, status
from rest_framework.decorators import (api_view, parser_classes,
                                       permission_classes)
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView
from utils import custom_viewsets
from utils.custom_permissions import (IsManipalAdminUser, IsPatientUser,
                                      IsSelfUserOrFamilyMember)
from utils.custom_sms import send_sms
from utils.payment_parameter_generator import get_payment_param
from utils.refund_parameter_generator import get_refund_param

from .exceptions import ProcessingIdDoesNotExistsValidationException
from .models import Payment
from .serializers import PaymentSerializer


class AppointmentPayment(APIView):
    def post(self, request, format=None):
        param = get_payment_param(request.data)
        location_code = request.data.get("location_code", None)
        try:
            hospital = Hospital.objects.get(code=location_code)
        except Exception:
            raise HospitalDoesNotExistsValidationException
        appointment = request.data["appointment_id"]
        registration_payment = request.data.get("registration_payment", False)
        appointment_instance = Appointment.objects.filter(
            appointment_identifier=appointment).first()
        if not appointment_instance:
            raise ValidationError("Appointment is not available")
        payment_data = {}
        param["token"]["appointment_id"] = appointment
        param["token"]["package_code"] = "NA"
        payment_data["processing_id"] = param["token"]["processing_id"]
        param["token"]["transaction_type"] = "APP"
        payment_data["appointment"] = appointment_instance.id
        payment_data["patient"] = request.user.id
        payment_data["payment_done_for_patient"] = appointment_instance.patient.id
        if appointment_instance.family_member:
            payment_data["payment_done_for_patient"] = None
            payment_data["payment_done_for_family_member"] = appointment_instance.family_member.id
        payment_data["location"] = hospital.id
        if registration_payment:
            payment_data["payment_for_uhid_creation"] = True
        payment = PaymentSerializer(data=payment_data)
        payment.is_valid(raise_exception=True)
        payment.save()
        return Response(data=param, status=status.HTTP_200_OK)


class HealthPackagePayment(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        param = get_payment_param(request.data)
        location_code = request.data.get("location_code", None)
        registration_payment = request.data.get("registration_payment", False)
        appointment = request.data["appointment_id"]
        family_member = request.data.get("user_id", None)
        try:
            hospital = Hospital.objects.get(code=location_code)
        except Exception:
            raise HospitalDoesNotExistsValidationException
        appointment_instance = HealthPackageAppointment.objects.filter(
            appointment_identifier=appointment).first()
        if not appointment_instance:
            raise ValidationError("Appointment is not available")
        package_code = request.data["package_code"]
        package_code_list = package_code.split(",")
        package_code = "||".join(package_code_list)
        payment_data = {}
        param["token"]["package_code"] = package_code
        param["token"]["appointment_id"] = appointment
        param["token"]["transaction_type"] = "HC"
        payment_data["processing_id"] = param["token"]["processing_id"]
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
        payment = PaymentSerializer(data=payment_data)
        payment.is_valid(raise_exception=True)
        payment.save()

        return Response(data=param, status=status.HTTP_200_OK)


class UHIDPayment(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        payment_data = {}
        family_member = request.data.get("user_id", None)
        location_code = request.data.get("location_code", None)
        try:
            hospital = Hospital.objects.get(code=location_code)
        except Exception:
            raise HospitalDoesNotExistsValidationException

        param = get_payment_param(request.data)
        param["token"]["transaction_type"] = "REG"
        param["token"]["payment_location"] = location_code
        payment_data["processing_id"] = param["token"]["processing_id"]
        payment_data["patient"] = request.user.id
        payment_data["location"] = hospital.id
        if family_member is not None:
            payment_data["payment_done_for_family_member"] = family_member
        else:
            payment_data["payment_done_for_patient"] = request.user.id
        payment_data["payment_for_uhid_creation"] = True
        payment = PaymentSerializer(data=payment_data)
        payment.is_valid(raise_exception=True)
        payment.save()
        return Response(data=param, status=status.HTTP_200_OK)


class OPBillPayment(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        payment_data = {}
        family_member = request.data.get("user_id", None)
        location_code = request.data.get("location_code", None)
        episode_no = request.data.get("episode_no", None)
        try:
            hospital = Hospital.objects.get(code=location_code)
        except Exception:
            raise HospitalDoesNotExistsValidationException

        param = get_payment_param(request.data)
        param["token"]["transaction_type"] = "OPB"
        param["token"]["appointment_id"] = episode_no
        param["token"]["payment_location"] = location_code
        payment_data["processing_id"] = param["token"]["processing_id"]
        payment_data["patient"] = request.user.id
        payment_data["location"] = hospital.id
        if family_member is not None:
            payment_data["payment_done_for_family_member"] = family_member
        else:
            payment_data["payment_done_for_patient"] = request.user.id
        payment_data["payment_for_op_billing"] = True
        payment_data["episode_number"] = episode_no
        payment = PaymentSerializer(data=payment_data)
        payment.is_valid(raise_exception=True)
        payment.save()
        return Response(data=param, status=status.HTTP_200_OK)


class IPDepositPayment(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        payment_data = {}
        family_member = request.data.get("user_id", None)
        location_code = request.data.get("location_code", None)
        try:
            hospital = Hospital.objects.get(code=location_code)
        except Exception:
            raise HospitalDoesNotExistsValidationException

        param = get_payment_param(request.data)
        param["token"]["transaction_type"] = "IPD"
        param["token"]["payment_location"] = location_code
        payment_data["processing_id"] = param["token"]["processing_id"]
        payment_data["patient"] = request.user.id
        payment_data["location"] = hospital.id
        if family_member is not None:
            payment_data["payment_done_for_family_member"] = family_member
        else:
            payment_data["payment_done_for_patient"] = request.user.id
        payment_data["payment_for_ip_deposit"] = True
        payment = PaymentSerializer(data=payment_data)
        payment.is_valid(raise_exception=True)
        payment.save()
        return Response(data=param, status=status.HTTP_200_OK)


class PaymentResponse(APIView):
    permission_classes = (AllowAny,)
    parser_classes = [FormParser, MultiPartParser, JSONParser]

    def post(self, request, format=None):
        response_token = request.data["responseToken"]
        response_token_json = json.loads(response_token)
        status_code = response_token_json["status_code"]
        payment_response = response_token_json["payment_response"]
        uhid = "-1"
        if status_code == 1200:
            processing_id = response_token_json["processing_id"]
            try:
                payment_instance = Payment.objects.get(
                    processing_id=processing_id)
            except Exception:
                raise ProcessingIdDoesNotExistsValidationException
            payment = {}
            payment_account = response_token_json["accounts"]
            payment["uhid_number"] = payment_account["account_number"]

            if payment_instance.appointment or payment_instance.payment_for_health_package:
                payment_paydetail = payment_response["payDetailAPIResponse"]
                if payment_paydetail["BillDetail"]:
                    bill_detail = json.loads(
                        payment_paydetail["BillDetail"])[0]
                    new_appointment_id = bill_detail["AppointmentId"]
                    payment["receipt_number"] = bill_detail["ReceiptNo"]

            if payment_instance.payment_for_uhid_creation:
                if payment_instance.appointment or payment_instance.payment_for_health_package:
                    payment_paydetail = payment_response["payDetailAPIResponse"]
                    if payment_paydetail["BillDetail"]:
                        bill_detail = json.loads(
                            payment_paydetail["BillDetail"])[0]
                        new_appointment_id = bill_detail["AppointmentId"]
                        payment["receipt_number"] = bill_detail["ReceiptNo"]
                else:
                    payment_paydetail = payment_response["pre_registration_response"]
                    payment["receipt_number"] = payment_paydetail["receiptNo"]

            if payment_instance.payment_for_ip_deposit:
                payment_paydetail = payment_response["onlinePatientDeposit"]
                if payment_paydetail["RecieptNumber"]:
                    bill_detail = json.loads(
                        payment_paydetail["RecieptNumber"])[0]
                    payment["receipt_number"] = bill_detail["ReceiptNo"]

            payment["status"] = payment_response["status"]
            payment["payment_method"] = payment_response["card_type"] + \
                "-" + payment_response["mode"]
            payment["transaction_id"] = payment_response["txnid"]
            payment["amount"] = payment_response["net_amount_debit"]
            payment["raw_info_from_salucro_response"] = response_token_json
            payment_serializer = PaymentSerializer(
                payment_instance, data=payment, partial=True)
            payment_serializer.is_valid(raise_exception=True)
            payment_serializer.save()
            uhid_info = {}
            if payment["uhid_number"] and payment["uhid_number"][:2] == "MH":
                uhid_info["uhid_number"] = payment["uhid_number"]
                uhid = payment["uhid_number"]
            if (payment_instance.payment_for_uhid_creation):
                if payment_instance.appointment:
                    appointment = Appointment.objects.filter(
                        id=payment_instance.appointment.id).first()
                    appointment.status = 6
                    appointment.save()
                if payment_instance.payment_done_for_patient:
                    patient = Patient.objects.filter(
                        id=payment_instance.payment_done_for_patient.id).first()
                    patient_serializer = PatientSpecificSerializer(
                        patient, data=uhid_info, partial=True)
                    patient_serializer.is_valid(raise_exception=True)
                    patient_serializer.save()
                if payment_instance.payment_done_for_family_member:
                    family_member = FamilyMember.objects.filter(
                        id=payment_instance.payment_done_for_family_member.id).first()
                    patient_serializer = FamilyMemberSpecificSerializer(
                        family_member, data=uhid_info, partial=True)
                    patient_serializer.is_valid(raise_exception=True)
                    patient_serializer.save()
            if payment_instance.appointment:
                appointment = Appointment.objects.filter(
                    id=payment_instance.appointment.id).first()
                update_data = {"payment_status": payment_response["status"]}
                update_data["consultation_amount"] = appointment.doctor.consultation_charges
                if payment_instance.payment_for_uhid_creation:
                    update_data["appointment_identifier"] = new_appointment_id
                    update_data["status"] = 1
                    update_data["uhid"] = payment["uhid_number"]
                appointment_serializer = AppointmentSerializer(
                    appointment, data=update_data, partial=True)
                appointment_serializer.is_valid(raise_exception=True)
                appointment_serializer.save()

            if payment_instance.payment_for_health_package:
                appointment = HealthPackageAppointment.objects.filter(
                    id=payment_instance.health_package_appointment.id).first()
                update_data = {}
                update_data["payment"] = payment_instance.id
                package_name = ""
                package_list = appointment.health_package.all()
                for package in package_list:
                    if not package_name:
                        package_name = package.name
                    else:
                        package_name = package_name + "," + package.name

                if payment_instance.payment_done_for_patient:
                    patient = Patient.objects.filter(
                        id=payment_instance.payment_done_for_patient.id).first()
                if payment_instance.payment_done_for_family_member:
                    family_member = FamilyMember.objects.filter(
                        id=payment_instance.payment_done_for_family_member.id).first()
                if payment_instance.payment_for_uhid_creation:
                    update_data["appointment_identifier"] = new_appointment_id
                appointment_serializer = HealthPackageAppointmentSerializer(
                    appointment, data=update_data, partial=True)
                appointment_serializer.is_valid(raise_exception=True)
                appointment_serializer.save()

        txnstatus = response_token_json["status_code"]
        txnamount = payment_response["net_amount_debit"]
        txnid = payment_response["txnid"]
        param = "?txnid={0}&txnstatus={1}&txnamount={2}&uhidNumber={3}".format(
            txnid, txnstatus, txnamount, uhid)
        return HttpResponseRedirect(settings.REDIRECT_URL + param)


class PaymentReturn(APIView):
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


class PaymentsAPIView(custom_viewsets.ReadOnlyModelViewSet):
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


class HealthPackageAPIView(custom_viewsets.ReadOnlyModelViewSet):
    search_fields = ['payment_id__payment_done_for_patient__first_name', 'payment_id__payment_done_for_family_member__first_name',
                     'payment_id__uhid_number', 'payment_id__payment_done_for_patient__mobile',
                     'payment_id__payment_done_for_family_member__mobile', 'payment_id__location__description',
                     'health_package__code','health_package__name']
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


class PayBillView(ProxyView):
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


class PayBillOpView(ProxyView):
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


class EpisodeItemView(ProxyView):
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


class RefundView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        param = get_refund_param(request.data)
        url = settings.REFUND_URL
        response = requests.post(url, data=param)
        data = json.loads(response.text)
        return Response(data=data)
