import base64
import hashlib
import json
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from random import randint

import requests
from django.contrib.auth.decorators import login_required
from django.core import serializers
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
from manipal_api.settings import (REDIRECT_URL, SALUCRO_AUTH_KEY,
                                  SALUCRO_AUTH_USER, SALUCRO_MID,
                                  SALUCRO_RESPONSE_URL, SALUCRO_RETURN_URL,
                                  SALUCRO_SECRET_KEY, SALUCRO_USERNAME)
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
from utils.payment_parameter_generator import get_payment_param

from .exceptions import ProcessingIdDoesNotExistsValidationException
from .models import Payment
from .serializers import PaymentSerializer


class AppointmentPayment(APIView):
    def post(self, request, format=None):
        param = get_payment_param(request.data)
        location_code = request.data.get("location_code", None)
        try:
            hospital = Hospital.objects.get(code=location_code)
        except Exception as e:
            raise HospitalDoesNotExistsValidationException
        appointment = request.data["appointment_id"]
        appointment_instance = Appointment.objects.filter(
            appointment_identifier=appointment).first()
        if not appointment_instance:
            raise ValidationError("Appointment is not available")
        payment_data = {}
        param["token"]["appointment_id"] = appointment
        payment_data["processing_id"] = param["token"]["processing_id"]
        param["token"]["transaction_type"] = "APP"
        payment_data["appointment"] = appointment_instance.id
        payment_data["patient"] = request.user.id
        payment_data["location"] = hospital.id
        payment = PaymentSerializer(data=payment_data)
        payment.is_valid(raise_exception=True)
        payment.save()
        return Response(data=param, status=status.HTTP_200_OK)


class HealthPackagePayment(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        param = get_payment_param(request.data)
        location_code = request.data.get("location_code", None)
        family_member = request.data.get("user_id", None)
        try:
            hospital = Hospital.objects.get(code=location_code)
        except Exception as e:
            raise HospitalDoesNotExistsValidationException
        package_code = request.data["package_code"]
        package_id = request.data["package_id"]
        package_id_list = package_id.split(",")
        package_code_list = package_code.split(",")
        package_code = "||".join(package_code_list)
        payment_data = {}
        param["token"]["package_code"] = package_code
        param["token"]["transaction_type"] = "HC"
        payment_data["processing_id"] = param["token"]["processing_id"]
        payment_data["health_package"] = package_id_list
        payment_data["patient"] = request.user.id
        payment_data["location"] = hospital.id
        payment_data["payment_for_health_package"] = True
        if family_member is not None:
            payment_data["payment_done_for_family_member"] = family_member
        else:
            payment_data["payment_done_for_patient"] = request.user.id
        payment = PaymentSerializer(data=payment_data)
        payment.is_valid(raise_exception=True)
        payment.save()
        appointment_data = {}
        appointment_data["payment"] = payment.data['id']
        appointment_data["hospital"] = hospital.id
        for package_id in package_id_list:
            appointment_data["health_package"] = package_id
            serializer = HealthPackageAppointmentSerializer(
                data=appointment_data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        return Response(data=param, status=status.HTTP_200_OK)


class UHIDPayment(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        payment_data = {}
        family_member = request.data.get("user_id", None)
        location_code = request.data.get("location_code", None)
        try:
            hospital = Hospital.objects.get(code=location_code)
        except Exception as e:
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
        return Response(data=param,status=status.HTTP_200_OK)


class PaymentResponse(APIView):
    permission_classes = (AllowAny,)
    parser_classes = [FormParser, MultiPartParser, JSONParser]

    def post(self, request, format=None):
        response_token = request.data["responseToken"]
        response_token_json = json.loads(response_token)
        processing_id = response_token_json["processing_id"]
        try:
            payment_instance = Payment.objects.get(processing_id=processing_id)
        except Exception as e:
            raise ProcessingIdDoesNotExistsValidationException
        payment = {}
        payment_response = response_token_json["payment_response"]
        payment_account = response_token_json["accounts"]
        payment["status"] = payment_response["status"]
        payment["transaction_id"] = payment_response["txnid"]
        payment["amount"] = payment_response["net_amount_debit"]
        payment["bank_ref_num"] = payment_response["bank_ref_num"]
        payment["uhid_number"] = payment_account["account_number"]
        payment["raw_info_from_salucro_response"] = response_token_json
        payment_serializer = PaymentSerializer(
            payment_instance, data=payment, partial=True)
        payment_serializer.is_valid(raise_exception=True)
        payment_serializer.save()
        uhid_info = {}
        uhid_info["uhid_number"] = payment_account["account_number"]
        uhid_info["pre_registration_number"] = None
        if (payment_instance.payment_done_for_patient or payment_instance.payment_done_for_family_member):
            if payment_instance.payment_done_for_patient:
                patient = Patient.objects.filter(
                    id=payment_instance.payment_done_for_patient.id).first()
                patient_serializer = PatientSpecificSerializer(
                    patient, data=uhid_info, partial=True)
                patient_serializer.is_valid(raise_exception=True)
                patient_serializer.save()
            else:
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
            appointment_serializer = AppointmentSerializer(
                appointment, data=update_data, partial=True)
            appointment_serializer.is_valid(raise_exception=True)
            appointment_serializer.save()
        txnstatus = response_token_json["status_code"]
        txnamount = payment_response["net_amount_debit"]
        txnid = payment_response["txnid"]
        param = "?txnid={0}&txnstatus={1}&txnamount={2}".format(
            txnid, txnstatus, txnamount)
        return HttpResponseRedirect(REDIRECT_URL + param)


class PaymentReturn(APIView):
    permission_classes = (AllowAny,)
    parser_classes = [FormParser, MultiPartParser, JSONParser]

    def post(self, request, format=None):
        data = request.data
        response_token = data["responseToken"]
        response_token_json = json.loads(response_token)
        payment_response = response_token_json["payment_response"]
        txnstatus = response_token_json["status_code"]
        txnamount = payment_response["net_amount_debit"]
        txnid = payment_response["txnid"]
        param = "?txnid={0}&txnstatus={1}&txnamount={2}".format(
            txnid, txnstatus, txnamount)
        return HttpResponseRedirect(REDIRECT_URL + param)


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
                return super().get_queryset().filter(uhid_number=uhid, created_at__week=current_week)
            elif filter_by == "last_week":
                last_week = date.today()-timedelta(days=7)
                return super().get_queryset().filter(uhid_number=uhid, created_at__gte=last_week)
            elif filter_by == "last_month":
                last_month = datetime.today() - timedelta(days=30)
                return super().get_queryset().filter(uhid_number=uhid, created_at__gte=last_month)
            else:
                return super().get_queryset().filter(uhid_number=uhid, created_at__date=filter_by)
        return super().get_queryset().filter(uhid_number=uhid)


class HealthPackageAPIView(custom_viewsets.ReadOnlyModelViewSet):
    search_fields = ['payment_id__payment_done_for_patient__first_name', 'payment_id__payment_done_for_family_member__first_name',
                     'payment_id__uhid_number', 'payment_id__payment_done_for_patient__mobile',
                     'payment_id__payment_done_for_family_member__mobile', 'payment_id__location__description',
                     'payment_id__health_package__code', 'payment_id__health_package__name']
    filter_backends = (filters.SearchFilter,
                       filters.OrderingFilter, DjangoFilterBackend)
    queryset = HealthPackageAppointment.objects.all()
    ordering = ('-payment_id__created_at',)
    serializer_class = HealthPackageAppointmentDetailSerializer
    permission_classes = [IsManipalAdminUser | IsSelfUserOrFamilyMember]
    list_success_message = 'Health Package list returned successfully!'

    def get_queryset(self):
        uhid = self.request.query_params.get("uhid", None)
        is_booked = self.request.query_params.get("is_booked", None)
        if ManipalAdmin.objects.filter(id=self.request.user.id).exists():
            return super().get_queryset().filter(payment_id__status="success")
        if is_booked:
            return super().get_queryset().filter(payment_id__uhid_number=uhid, payment_id__status="success", appointment_status="Booked")
        return super().get_queryset().filter(payment_id__uhid_number=uhid, payment_id__status="success")


class PayBillView(ProxyView):
    source = 'DepositAmt'
    permission_classes = [IsSelfUserOrFamilyMember]

    def get_request_data(self, request):
        data = request.data
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
        data = request.data
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
        data = request.data
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
                episode_response = root.find("EpisodeList")
                response_data = json.loads(episode_response.text)

        return self.custom_success_response(message=response_message,
                                            success=success_status, data=response_data)
