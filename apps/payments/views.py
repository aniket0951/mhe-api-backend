import base64
import hashlib
import json
import xml.etree.ElementTree as ET
from random import randint

import requests
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render

from apps.manipal_admin.models import ManipalAdmin
from apps.patients.exceptions import PatientDoesNotExistsValidationException
from apps.patients.models import FamilyMember, Patient
from apps.patients.serializers import FamilyMemberSerializer, PatientSerializer
from manipal_api.settings import (SALUCRO_AUTH_KEY, SALUCRO_AUTH_USER,
                                  SALUCRO_MID, SALUCRO_RESPONSE_URL,
                                  SALUCRO_RETURN_URL, SALUCRO_SECRET_KEY,
                                  SALUCRO_USERNAME)
from proxy.custom_views import ProxyView
from rest_framework import filters
from rest_framework.decorators import (api_view, parser_classes,
                                       permission_classes)
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from utils import custom_viewsets
from utils.custom_permissions import (IsManipalAdminUser, IsPatientUser,
                                      IsSelfUserOrFamilyMember)
from utils.payment_parameter_generator import get_payment_param

from .exceptions import ProcessingIdDoesNotExistsValidationException
from .models import Payment
from .serializers import PaymentSerializer
from apps.appointments.models import Appointment
from apps.appointments.serializers import AppointmentSerializer


class AppointmentPayment(APIView):
    def post(self, request, format=None):
        param = get_payment_param(request.data)
        appointment_id = request.data["appointment_id"]
        payment_data = {}
        param["token"]["appointment_id"] = appointment_id
        payment_data["processing_id"] = param["token"]["processing_id"]
        param["token"]["transaction_type"] = "APP"
        payment_data["appointment_id"] = appointment_id
        payment_data["patient"] = request.user.id
        payment = PaymentSerializer(data=payment_data)
        payment.is_valid(raise_exception=True)
        payment.save()
        return Response(data=param)


class HealthPackagePayment(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        param = get_payment_param(request.data)
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
        payment = PaymentSerializer(data=payment_data)
        payment.is_valid(raise_exception=True)
        payment.save()
        return Response(data=param)


class UHIDPayment(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        payment_data = {}
        family_member = request.data.get("user_id", None)
        param = get_payment_param(request.data)
        payment_data["processing_id"] = param["token"]["processing_id"]
        payment_data["patient"] = request.user.id
        if family_member is not None:
            payment_data["uhid_family_member"] = family_member
        else:
            payment_data["uhid_patient"] = request.user.id
        payment = PaymentSerializer(data=payment_data)
        payment.is_valid(raise_exception=True)
        payment.save()
        return Response(data=param)


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
        if (payment_instance.uhid_patient or payment_instance.uhid_family_member):
            if payment_instance.uhid_patient:
                patient = Patient.objects.filter(
                    id=payment_instance.uhid_patient).first()
                patient_serializer = PatientSerializer(
                    patient, data=uhid_info, partial=True)
                patient_serializer.is_valid(raise_exception=True)
                patient_serializer.save()
            else:
                family_member = FamilyMember.objects.filter(
                    id=payment_instance.uhid_family_member).first()
                patient_serializer = FamilyMemberSerializer(
                    family_member, data=uhid_info, partial=True)
                patient_serializer.is_valid(raise_exception=True)
                patient_serializer.save()
        if payment_instance.appointment_identifier:
            appointment = Appointment.objects.filter(id = payment_instance.appointment_identifier_id)
            update_data = {"payment_status": payment_response["status"]}
            appointment_serializer = AppointmentSerializer(appointment, data = update_data, partial = True)
            appointment_serializer.is_valid(raise_exception = True)
            appointment_serializer.save()

        return Response(payment_serializer.data)


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
        return HttpResponseRedirect("https://mhedev.mantralabsglobal.com/redirect"+param)


class PaymentsAPIView(custom_viewsets.ReadOnlyModelViewSet):
    search_fields = ['patient__first_name']
    filter_backends = (filters.SearchFilter,)
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsManipalAdminUser | IsSelfUserOrFamilyMember]
    list_success_message = 'Payment list returned successfully!'
    retrieve_success_message = 'Payment information returned successfully!'

    def get_queryset(self):
        uhid = self.request.query_params.get("uhid", None)
        if ManipalAdmin.objects.filter(id=self.request.user.id).exists():
            return super().get_queryset()
        return super().get_queryset().filter(uhid_number=uhid)
