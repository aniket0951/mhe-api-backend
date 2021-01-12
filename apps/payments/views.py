import json
import logging
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required

from django.db.models import Q
from django.http import HttpResponseRedirect

from apps.appointments.models import Appointment, HealthPackageAppointment
from apps.appointments.serializers import (
                        AppointmentSerializer, 
                        HealthPackageAppointmentDetailSerializer,
                        HealthPackageAppointmentSerializer
                    )
from apps.manipal_admin.models import ManipalAdmin
from apps.master_data.exceptions import HospitalDoesNotExistsValidationException
from apps.master_data.models import Hospital
from apps.patients.models import FamilyMember, Patient
from apps.patients.serializers import (FamilyMemberSpecificSerializer,PatientSpecificSerializer)
from proxy.custom_serializables import EpisodeItems as serializable_EpisodeItems
from proxy.custom_serializables import IPBills as serializable_IPBills
from proxy.custom_serializables import OPBills as serializable_OPBills
from proxy.custom_serializables import CorporateRegistration as serializable_CorporateRegistration
from proxy.custom_serializers import ObjectSerializer as custom_serializer
from proxy.custom_views import ProxyView

from rest_framework import filters, status
from rest_framework.decorators import (api_view, parser_classes,permission_classes)
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.test import APIClient
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from utils import custom_viewsets
from utils.custom_permissions import (IsManipalAdminUser, IsPatientUser, IsSelfUserOrFamilyMember)
from utils.payment_parameter_generator import get_payment_param
from utils.refund_parameter_generator import get_refund_param

from .exceptions import ProcessingIdDoesNotExistsValidationException
from .models import Payment, PaymentReceipts, PaymentRefund
from .serializers import (PaymentReceiptsSerializer, PaymentRefundSerializer, PaymentSerializer)

logger = logging.getLogger('django')
client = APIClient()


class AppointmentPayment(APIView):
    permission_classes = (IsPatientUser,)

    def post(self, request, format=None):
        param = get_payment_param(request.data)
        location_code = request.data.get("location_code", None)
        try:
            hospital = Hospital.objects.filter(code=location_code).first()
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

        calculated_amount = 0
        payment_data["location"] = hospital.id
        uhid = appointment_instance.uhid
        order_date = appointment_instance.appointment_date.strftime("%d%m%Y")
        if registration_payment:
            uhid = "None"
            payment_data["payment_for_uhid_creation"] = True
            response = client.post('/api/master_data/items_tariff_price',
                                   json.dumps({'item_code': 'AREG001', 'location_code': location_code}), content_type='application/json')

            if response.status_code == 200 and response.data["success"] == True:
                calculated_amount += int(float(response.data["data"][0]["ItemPrice"]))

        response_doctor_charges = client.post('/api/master_data/consultation_charges',
                                              json.dumps({'location_code': location_code, 'specialty_code': appointment_instance.department.code, 'doctor_code': appointment_instance.doctor.code, "uhid":uhid, 'order_date': order_date}), content_type='application/json')


        if response_doctor_charges.status_code == 200 and response_doctor_charges.data["success"] == True:
            
            if appointment_instance.appointment_mode == "HV":
                calculated_amount = calculated_amount + \
                    int(float(response_doctor_charges.data["data"]["OPDConsCharges"]))

            if appointment_instance.appointment_mode == "VC":
                calculated_amount = calculated_amount + \
                    int(float(response_doctor_charges.data["data"]["VCConsCharges"]))

            if appointment_instance.appointment_mode == "PR":
                calculated_amount = calculated_amount + \
                    int(float(response_doctor_charges.data["data"]["PRConsCharges"]))

        if not (calculated_amount == int(float(param["token"]["accounts"][0]["amount"]))):
            raise ValidationError("Price is Updated")

        payment = PaymentSerializer(data=payment_data)
        payment.is_valid(raise_exception=True)
        payment.save()
        logger.info(param)
        return Response(data=param, status=status.HTTP_200_OK)


class HealthPackagePayment(APIView):
    permission_classes = (IsPatientUser,)

    def post(self, request, format=None):
        param = get_payment_param(request.data)
        location_code = request.data.get("location_code", None)
        registration_payment = request.data.get("registration_payment", False)
        appointment = request.data.get("appointment_id", None)
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

        calculated_amount = 0
        for package in package_code_list:
            response = client.post('/api/health_packages/health_package_price',
                                   json.dumps({'location_code': location_code, 'package_code': package}), content_type='application/json')

            if response.status_code == 200 and response.data["success"] == True:
                calculated_amount += int(float(response.data["message"]))

        if not (calculated_amount == int(float(param["token"]["accounts"][0]["amount"]))):
            raise ValidationError("Price is Updated")

        if family_member is not None:
            payment_data["payment_done_for_family_member"] = family_member
        else:
            payment_data["payment_done_for_patient"] = request.user.id
        payment = PaymentSerializer(data=payment_data)
        payment.is_valid(raise_exception=True)
        payment.save()
        logger.info(param)
        return Response(data=param, status=status.HTTP_200_OK)


class UHIDPayment(APIView):
    permission_classes = (IsPatientUser,)

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

        calculated_amount = 0
        response = client.post('/api/master_data/items_tariff_price',
                               json.dumps({'item_code': 'AREG001', 'location_code': location_code}), content_type='application/json')

        if response.status_code == 200 and response.data["success"] == True:
            calculated_amount += int(float(response.data["data"][0]["ItemPrice"]))

        if not (calculated_amount == int(float(param["token"]["accounts"][0]["amount"]))):
            raise ValidationError("Price is Updated")

        payment_data["payment_for_uhid_creation"] = True
        payment = PaymentSerializer(data=payment_data)
        payment.is_valid(raise_exception=True)
        payment.save()
        logger.info(param)
        return Response(data=param, status=status.HTTP_200_OK)


class OPBillPayment(APIView):
    permission_classes = (IsPatientUser,)

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

        response = client.post('/api/payments/op_bill_details',
                               json.dumps({"uhid": param["token"]["accounts"][0]["account_number"], 'location_code': location_code}), content_type='application/json')
        calculated_amount = 0
        if response.status_code == 200 and response.data["success"] == True:
            if response.data["data"]:
                episode_list = response.data["data"]
                for episode in episode_list:
                    if episode["EpisodeNo"] == episode_no:
                        calculated_amount += int(float(episode["OutStandingAmt"]))

        if not (calculated_amount == int(float(param["token"]["accounts"][0]["amount"]))):
            raise ValidationError("Price is Updated")

        payment = PaymentSerializer(data=payment_data)
        payment.is_valid(raise_exception=True)
        payment.save()
        logger.info(param)
        return Response(data=param, status=status.HTTP_200_OK)


class IPDepositPayment(APIView):
    permission_classes = (IsPatientUser,)

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
        logger.info(param)
        return Response(data=param, status=status.HTTP_200_OK)


class PaymentResponse(APIView):
    permission_classes = (AllowAny,)
    parser_classes = [FormParser, MultiPartParser, JSONParser]

    def post(self, request, format=None):
        logger.info(request.data)
        response_token = request.data["responseToken"]
        response_token_json = json.loads(response_token)
        status_code = response_token_json["status_code"]
        payment_response = response_token_json["payment_response"]
        processing_id = response_token_json["processing_id"]
        payment_account = response_token_json["accounts"]
        try:
            payment_instance = Payment.objects.get(
                processing_id=processing_id)
        except Exception:
            raise ProcessingIdDoesNotExistsValidationException
        uhid = "-1"
        payment_instance.raw_info_from_salucro_response = response_token_json
        payment_instance.save()
        
        if status_code == 1200:
            payment = {}
            payment["uhid_number"] = payment_account["account_number"]
            if payment["uhid_number"]:
                payment["uhid_number"] = payment["uhid_number"].upper()

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

            if payment_instance.payment_for_op_billing:
                payment_paydetail = payment_response["opPatientBilling"]
                if payment_paydetail["BillDetail"]:
                    bill_detail = json.loads(
                        payment_paydetail["BillDetail"])[0]
                    payment["receipt_number"] = bill_detail["BillNo"]
                    payment["episode_number"] = bill_detail["EpisodeNo"]

            payment["status"] = payment_response["status"]
            payment["payment_method"] = payment_response["card_type"] + \
                "-" + payment_response["mode"]
            payment["transaction_id"] = payment_response["txnid"]
            payment["amount"] = payment_response["net_amount_debit"]
            payment_serializer = PaymentSerializer(
                payment_instance, data=payment, partial=True)
            payment_serializer.is_valid(raise_exception=True)
            payment_serializer.save()
            uhid_info = {}
            if payment["uhid_number"] and (payment["uhid_number"][:2] == "MH" or payment["uhid_number"][:3] == "MMH"):
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
                update_data["consultation_amount"] = payment_instance.amount
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

        appointment_identifier = request.data.get(
            "appointment_identifier", None)
        appointment_instance = Appointment.objects.filter(
            appointment_identifier=appointment_identifier).first()
        if appointment_instance.payment_appointment.exists():
            param = get_refund_param(request.data)
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


class AppointmentPaymentView(ProxyView):
    permission_classes = [AllowAny]
    source = 'OnlinePayment'

    def get_request_data(self, request):
        request_xml = serializable_PaymentUpdate(request.data)
        request_data = custom_serializer().serialize(request_xml, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response.content)
        status = root.find("Status").text
        message = root.find("Message").text
        success_status = False
        data = dict()
        if status == '1':
            bill_detail = root.find("BillDetail").text
            data["payDetailAPIResponse"] = dict()
            data["payDetailAPIResponse"]["BillDetail"] = bill_detail
            if bill_detail:
                app_id = self.request.data.get("app_id")
                aap_list = ast.literal_eval(bill_detail)
                if aap_list:
                    appointment_identifier = aap_list[0].get("AppointmentId")
                    appointment_instance = Appointment.objects.filter(
                        appointment_identifier=app_id).first()
                    if appointment_instance:
                        success_status = True
                        appointment_instance.payment_status = "success"
                        if appointment_identifier:
                            appointment_instance.appointment_identifier = appointment_identifier
                        appointment_instance.save()
        return self.custom_success_response(message=message,
                                            success=success_status, data=data)

class UHIDPaymentView(ProxyView):
    permission_classes = [AllowAny]
    source = 'PaymentForRegistration'

    def get_request_data(self, request):
        request_xml = serializable_UHIDPaymentUpdate(request.data)
        request_data = custom_serializer().serialize(request_xml, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response.content)
        status = root.find("Status").text
        message = root.find("Message").text
        success_status = False
        data = dict()
        if status == '1':
            success_status = True
            data["uhid_number"] = root.find("UID").text 
            data["ReceiptNo"] = root.find("ReceiptNo").text 
        return self.custom_success_response(message=message,
                                            success=success_status, data=data)

class OPBillingPaymentView(ProxyView):
    permission_classes = [AllowAny]
    source = 'OPBilling'

    def get_request_data(self, request):
        request_xml = serializable_OPBillingPaymentUpdate(request.data)
        request_data = custom_serializer().serialize(request_xml, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response.content)
        status = root.find("Status").text
        message = root.find("Message").text
        success_status = False
        data = dict()
        if status == '1':
            bill_detail = root.find("BillDetail").text
            success_status = True
            data["payDetailAPIResponse"] = dict()
            data["payDetailAPIResponse"]["BillDetail"] = bill_detail
        return self.custom_success_response(message=message,
                                            success=success_status, data=data)

class IPDepositPaymentView(ProxyView):
    permission_classes = [AllowAny]
    source = 'InsertOnlinePatientDeposit'

    def get_request_data(self, request):
        request_xml = serializable_IPDepositPaymentUpdate(request.data)
        request_data = custom_serializer().serialize(request_xml, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response.content)
        status = root.find("Status").text
        message = root.find("Message").text
        success_status = False
        data = dict()
        if status == '1':
            reciept_number = root.find("RecieptNumber").text
            success_status = True
            data["payDetailAPIResponse"] = dict()
            data["payDetailAPIResponse"]["RecieptNumber"] = reciept_number
        return self.custom_success_response(message=message,
                                            success=success_status, data=data)

class CheckAppointmentPaymentStatusView(ProxyView):
    permission_classes = [AllowAny]
    source = 'checkAppPaymentStatus'

    def get_request_data(self, request):
        request_xml = serializable_CheckAppointmentPaymentStatus(request.data)
        request_data = custom_serializer().serialize(request_xml, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response.content)
        check_app_payment_status_response = root.find("checkAppPaymentStatusResponse").text
        data = dict()
        if check_app_payment_status_response:
            data.update(json.loads(check_app_payment_status_response))
        return self.custom_success_response(
                                message="checkAppPaymentStatus",
                                success=True,
                                data=data
                            )