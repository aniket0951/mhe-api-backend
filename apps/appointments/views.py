import ast
import base64
import datetime
import hashlib
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

import requests
from django.conf import settings
from django.db.models import Q
from django.shortcuts import render

import rest_framework
from apps.doctors.exceptions import DoctorDoesNotExistsValidationException
from apps.doctors.models import Doctor
from apps.health_packages.exceptions import FeatureNotAvailableException
from apps.manipal_admin.models import ManipalAdmin
from apps.master_data.exceptions import (
    DepartmentDoesNotExistsValidationException,
    HospitalDoesNotExistsValidationException)
from apps.master_data.models import Department, Hospital, Specialisation
from apps.notifications.utils import (cancel_parameters,
                                      doctor_rebook_parameters)
from apps.patients.exceptions import PatientDoesNotExistsValidationException
from apps.patients.models import FamilyMember, Patient
from apps.payments.views import RefundView
from apps.users.models import BaseUser
from django_filters.rest_framework import DjangoFilterBackend
from proxy.custom_serializables import BookMySlot as serializable_BookMySlot
from proxy.custom_serializables import \
    CancelAppointmentRequest as serializable_CancelAppointmentRequest
from proxy.custom_serializables import \
    CurrentPatientList as serializable_CurrentPatientList
from proxy.custom_serializables import \
    RescheduleAppointment as serializable_RescheduleAppointment
from proxy.custom_serializables import \
    UpdateCancelAndRefund as serializable_UpdateCancelAndRefund
from proxy.custom_serializables import \
    UpdateRebookStatus as serializable_UpdateRebookStatus
from proxy.custom_serializers import ObjectSerializer as custom_serializer
from proxy.custom_views import ProxyView
from rest_framework import filters, generics, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView
from utils import custom_viewsets
from utils.custom_permissions import (InternalAPICall, IsDoctor,
                                      IsManipalAdminUser, IsPatientUser,
                                      IsSelfUserOrFamilyMember, SelfUserAccess)

from .exceptions import (AppointmentAlreadyExistsException,
                         AppointmentDoesNotExistsValidationException)
from .models import (Appointment, AppointmentDocuments,
                     AppointmentPrescription, AppointmentVital,
                     CancellationReason, Feedbacks, HealthPackageAppointment,
                     PrescriptionDocuments)
from .serializers import (AppointmentDocumentsSerializer,
                          AppointmentPrescriptionSerializer,
                          AppointmentSerializer, AppointmentVitalSerializer,
                          CancellationReasonSerializer, FeedbacksSerializer,
                          HealthPackageAppointmentSerializer,
                          PrescriptionDocumentsSerializer)
from .utils import cancel_and_refund_parameters, rebook_parameters

logger = logging.getLogger('django')


class AppointmentsAPIView(custom_viewsets.ReadOnlyModelViewSet):
    search_fields = ['patient__first_name', 'doctor__name', 'family_member__first_name',
                     'appointment_identifier', 'patient__uhid_number', 'family_member__uhid_number',
                     'patient__mobile', 'patient__email']
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)

    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsManipalAdminUser | IsSelfUserOrFamilyMember]
    filter_fields = ('status', 'appointment_identifier')
    ordering = ('appointment_date', '-appointment_slot', 'status')
    ordering_fields = ('appointment_date', 'appointment_slot', 'status')
    create_success_message = None
    list_success_message = 'Appointment list returned successfully!'
    retrieve_success_message = 'Appointment information returned successfully!'
    update_success_message = None

    def get_queryset(self):
        qs = super().get_queryset()
        family_member = self.request.query_params.get("user_id", None)
        is_upcoming = self.request.query_params.get("is_upcoming", False)
        is_cancelled = self.request.query_params.get("is_cancelled", False)
        if ManipalAdmin.objects.filter(id=self.request.user.id).exists():
            date_from = self.request.query_params.get("date_from", None)
            date_to = self.request.query_params.get("date_to", None)
            if date_from and date_to:
                qs = qs.filter(appointment_date__range=[date_from, date_to])
            if is_cancelled == "true":
                return qs.filter(status=2)
            if is_cancelled == "false":
                return qs.filter(appointment_date__gte=datetime.now().date(), status=1)
            return qs

        elif (family_member is not None):
            member = FamilyMember.objects.filter(id=family_member).first()
            if not member:
                raise ValidationError("Family Member does not Exist")
            member_uhid = member.uhid_number
            if is_upcoming:
                return super().get_queryset().filter(
                    Q(appointment_date__gte=datetime.now().date()) & Q(status=1) & ((Q(uhid__isnull=False) & Q(uhid=member_uhid)) | Q(family_member_id=family_member))).exclude(
                    Q(appointment_mode="VC") & (Q(vc_appointment_status="4") | Q(payment_status__isnull=True)))
            return super().get_queryset().filter(
                (Q(appointment_date__lt=datetime.now().date()) | Q(status=2) | Q(status=5) | Q(vc_appointment_status="4")) & ((Q(uhid__isnull=False) & Q(uhid=member_uhid)) | Q(family_member_id=family_member)))
        else:
            patient = Patient.objects.filter(id=self.request.user.id).first()
            if not patient:
                raise ValidationError("Patient does not Exist")
            member_uhid = patient.uhid_number
            if is_upcoming:
                return super().get_queryset().filter(
                    Q(appointment_date__gte=datetime.now().date()) & Q(status=1)
                    & ((Q(uhid__isnull=False) & Q(uhid=member_uhid)) | (Q(patient_id=patient.id)
                                                                        & Q(family_member__isnull=True)))).exclude(
                    Q(appointment_mode="VC") & (Q(vc_appointment_status="4") | Q(payment_status__isnull=True)))
            return super().get_queryset().filter(
                (Q(appointment_date__lt=datetime.now().date())
                 | Q(status=2) | Q(status=5) | Q(vc_appointment_status="4"))
                & ((Q(uhid__isnull=False) & Q(uhid=member_uhid))
                   | (Q(patient_id=patient.id)) &
                   Q(family_member__isnull=True)))


class CreateMyAppointment(ProxyView):
    permission_classes = [IsPatientUser | InternalAPICall]
    source = 'bookAppointment'

    def get_request_data(self, request):

        patient_id = request.user.id
        family_member_id = request.data.pop("user_id", None)
        amount = request.data.pop("amount", None)
        patient = Patient.objects.filter(id=patient_id).first()
        family_member = FamilyMember.objects.filter(
            id=family_member_id).first()
        if not patient:
            raise PatientDoesNotExistsValidationException
        hospital = Hospital.objects.filter(
            id=request.data.pop("hospital_id")).first()
        if not hospital:
            raise HospitalDoesNotExistsValidationException
        doctor = Doctor.objects.filter(
            id=request.data.pop("doctor_id")).first()
        if not doctor:
            raise DoctorDoesNotExistsValidationException
        department = Department.objects.filter(
            id=request.data.pop("department_id")).first()
        if not department:
            raise DepartmentDoesNotExistsValidationException

        if family_member:
            user = family_member
        else:
            user = patient

        request.data['doctor_code'] = doctor.code
        request.data['location_code'] = hospital.code
        request.data['patient_name'] = user.first_name
        request.data['mobile'] = str(user.mobile)
        request.data['email'] = str(user.email)
        request.data['speciality_code'] = department.code

        slot_book = serializable_BookMySlot(request.data)
        request_data = custom_serializer().serialize(slot_book, 'XML')

        request.data["patient"] = patient
        request.data["family_member"] = family_member
        request.data["hospital"] = hospital
        request.data["doctor"] = doctor
        request.data["department"] = department
        request.data["consultation_amount"] = amount
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        response_message = "Unable to Book the Appointment. Please try again"
        response_data = {}
        response_success = False
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            appointment_identifier = root.find("appointmentIdentifier").text
            status = root.find("Status").text
            if status == "FAILED":
                message = root.find("Message").text
                raise ValidationError(message)
            else:
                data = self.request.data
                family_member = data.get("family_member")
                new_appointment = {}
                appointment_date_time = data.pop("appointment_date_time")
                datetime_object = datetime.strptime(
                    appointment_date_time, '%Y%m%d%H%M%S')
                time = datetime_object.time()
                new_appointment["appointment_date"] = datetime_object.date()
                new_appointment["appointment_slot"] = time.strftime(
                    "%H:%M:%S %p")
                new_appointment["status"] = 1
                new_appointment["appointment_identifier"] = appointment_identifier
                new_appointment["patient"] = data.get("patient").id
                new_appointment["uhid"] = data.get("patient").uhid_number
                new_appointment["department"] = data.get("department").id
                new_appointment["consultation_amount"] = data.get(
                    "consultation_amount")
                if family_member:
                    new_appointment["family_member"] = family_member.id
                    new_appointment["uhid"] = family_member.uhid_number
                new_appointment["doctor"] = data.get("doctor").id
                new_appointment["hospital"] = data.get("hospital").id
                new_appointment["appointment_mode"] = data.get(
                    "appointment_mode", None)
                appointment = AppointmentSerializer(data=new_appointment)
                appointment.is_valid(raise_exception=True)
                appointment.save()
                response_success = True
                response_message = "Appointment has been created"
                response_data["appointment_identifier"] = appointment_identifier

        return self.custom_success_response(message=response_message,
                                            success=response_success, data=response_data)


class CancelMyAppointment(ProxyView):
    source = 'cancelAppointment'
    permission_classes = [IsPatientUser | IsManipalAdminUser | InternalAPICall]

    def get_request_data(self, request):
        data = request.data
        appointment_id = data.get("appointment_identifier")
        reason_id = data.pop("reason_id")
        status = data.pop("status", None)
        instance = Appointment.objects.filter(
            appointment_identifier=appointment_id).first()
        if not instance:
            raise AppointmentDoesNotExistsValidationException
        other_reason = data.pop("other", None)
        request.data["location_code"] = instance.hospital.code
        cancel_appointment = serializable_CancelAppointmentRequest(
            **request.data)
        request_data = custom_serializer().serialize(cancel_appointment, 'XML')
        data["reason_id"] = reason_id
        data["status"] = status
        data["other_reason"] = other_reason
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        appointment_id = self.request.data.get("appointment_identifier")
        root = ET.fromstring(response.content)
        response_message = "We are unable to cancel the appointment. Please Try again"
        success_status = False
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            status = root.find("Status").text
            message = root.find("Message").text
            response_message = status
            if status == "SUCCESS":
                instance = Appointment.objects.filter(
                    appointment_identifier=appointment_id).first()
                if not instance:
                    raise AppointmentDoesNotExistsValidationException
                instance.status = 2
                if self.request.data.get("status"):
                    instance.status = self.request.data.get("status")
                instance.reason_id = self.request.data.get("reason_id")
                instance.other_reason = self.request.data.get("other_reason")
                instance.save()
                refund_param = cancel_and_refund_parameters(
                    {"appointment_identifier": instance.appointment_identifier})
                response = RefundView.as_view()(refund_param)
                param = dict()
                param["app_id"] = instance.appointment_identifier
                param["cancel_remark"] = instance.reason.reason
                param["location_code"] = instance.hospital.code
                if instance.payment_appointment.exists():
                    payment_instance = instance.payment_appointment.filter(
                        status="Refunded").first()
                    if payment_instance:
                        if payment_instance.payment_refund.exists():
                            refund_instance = payment_instance.payment_refund.filter(
                                status="success").first()
                            if refund_instance:
                                param["refund_status"] = "Y"
                                param["refund_trans_id"] = refund_instance.transaction_id
                                param["refund_amount"] = str(
                                    (int(refund_instance.amount)))
                                param["refund_time"] = refund_instance.created_at.time().strftime(
                                    "%H:%M")
                                param["refund_date"] = refund_instance.created_at.date().strftime(
                                    "%d/%m/%Y")
                request_param = cancel_and_refund_parameters(param)
                response = CancelAndRefundView.as_view()(request_param)
                success_status = True
                return self.custom_success_response(message=response_message,
                                                    success=success_status, data=None)
        raise ValidationError(
            "Could not process the request. PLease try again")


class RecentlyVisitedDoctorlistView(custom_viewsets.ReadOnlyModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsPatientUser]
    create_success_message = None
    list_success_message = 'Appointment list returned successfully!'
    retrieve_success_message = 'Appointment information returned successfully!'
    update_success_message = None

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(patient_id=self.request.user.id, hospital_id=self.request.query_params.get("location_id", None)).distinct('doctor__code')


class CancellationReasonlistView(custom_viewsets.ReadOnlyModelViewSet):
    queryset = CancellationReason.objects.all()
    serializer_class = CancellationReasonSerializer
    permission_classes = [AllowAny]

    list_success_message = 'Cancellation Reason list returned successfully!'
    retrieve_success_message = 'Cancellation Reason returned successfully!'


class HealthPackageAppointmentView(ProxyView):
    permission_classes = [IsPatientUser | InternalAPICall]
    source = 'bookAppointment'

    def get_request_data(self, request):
        param = dict()
        patient_id = request.user.id
        family_member_id = request.data.get("user_id", None)
        package_id = request.data["package_id"]
        package_id_list = package_id.split(",")
        previous_appointment = request.data.get("previous_appointment", None)
        payment_id = request.data.get("payment_id", None)
        if previous_appointment and payment_id:
            appointment_instance = HealthPackageAppointment.objects.filter(
                appointment_identifier=previous_appointment).first()
            if not appointment_instance:
                raise ValidationError("Appointment does not Exist")
            serializer = HealthPackageAppointmentSerializer(
                appointment_instance, data={"appointment_status": "ReBooked"}, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        health_package_appointment = HealthPackageAppointmentSerializer(data={"patient": patient_id, "family_member": family_member_id,
                                                                              "hospital": request.data.get("hospital_id"), "health_package": package_id_list,
                                                                              "payment": payment_id})
        health_package_appointment.is_valid(raise_exception=True)
        request.data["appointment_instance"] = health_package_appointment.save()
        hospital = Hospital.objects.filter(
            id=request.data.get("hospital_id", None)).first()
        if not hospital.is_health_package_online_purchase_supported:
            raise FeatureNotAvailableException
        param["location_code"] = hospital.code
        param["doctor_code"] = hospital.health_package_doctor_code
        param["speciality_code"] = hospital.health_package_department_code
        param["appointment_date_time"] = request.data.get(
            "appointment_date_time", None)
        param["mrn"] = request.data.get("mrn")
        param["patient_name"] = request.data.get("patient_name")
        param["mobile"] = request.data.get("mobile")
        param["email"] = request.data.get("email")

        slot_book = serializable_BookMySlot(param)
        request_data = custom_serializer().serialize(slot_book, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        response_message = "Unable to Book the Appointment. Please try again"
        response_data = {}
        response_success = False
        instance = self.request.data["appointment_instance"]
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            appointment_identifier = root.find("appointmentIdentifier").text
            status = root.find("Status").text
            if status == "FAILED":
                instance.delete()
                message = root.find("Message").text
                raise ValidationError(message)
            else:
                datetime_object = datetime.strptime(
                    self.request.data["appointment_date_time"], '%Y%m%d%H%M%S')
                new_appointment = dict()
                new_appointment["appointment_date"] = datetime_object
                new_appointment["appointment_status"] = "Booked"
                new_appointment["appointment_identifier"] = appointment_identifier
                appointment = HealthPackageAppointmentSerializer(
                    instance, data=new_appointment, partial=True)
                appointment.is_valid(raise_exception=True)
                appointment.save()
                if self.request.data.get("previous_appointment"):
                    payment_obj = instance.payment
                    payment_obj.health_package_appointment = instance
                    payment_obj.save()
                    request_param = rebook_parameters(instance)
                    response = ReBookView.as_view()(request_param)
                response_success = True
                response_message = "Health Package Appointment has been created"
                response_data["appointment_identifier"] = appointment_identifier
            return self.custom_success_response(message=response_message,
                                                success=response_success, data=response_data)
        instance.delete()
        raise ValidationError(
            "Could not process your request. Please try again")


class OfflineAppointment(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        logger.info(request.data)
        required_keys = ['UHID', 'doctorCode', 'appointmentIdentifier', 'appointmentDatetime',
                         'locationCode', 'status', 'payment_status', 'department']
        data = request.data
        appointment_data = dict()
        if not (data and set(required_keys).issubset(set(data.keys()))):
            return Response({"message": "Mandatory parameter is missing"},
                            status=status.HTTP_200_OK)
        uhid = data["UHID"]
        deparmtment_code = data["department"]
        if not (uhid and deparmtment_code and data["doctorCode"] and
                data["locationCode"] and data["appointmentDatetime"] and data["appointmentIdentifier"]):
            return Response({"message": "Mandatory parameter is missing"},
                            status=status.HTTP_200_OK)
        patient = Patient.objects.filter(uhid_number=uhid).first()
        family_member = FamilyMember.objects.filter(uhid_number=uhid).first()
        doctor = Doctor.objects.filter(code=data["doctorCode"].upper()).first()
        hospital = Hospital.objects.filter(code=data["locationCode"]).first()
        department = Department.objects.filter(code=deparmtment_code).first()
        if not (patient or family_member):
            return Response({"message": "User is not App user"}, status=status.HTTP_200_OK)
        if not (doctor and hospital and department):
            return Response({"message": "Hospital/doctor/department is not available"}, status=status.HTTP_200_OK)
        appointment_identifier = data["appointmentIdentifier"].replace(
            "*", "|")
        appointment_data["patient"] = patient
        if family_member:
            appointment_data["patient"] = family_member.patient_info.id
            appointment_data["family_member"] = family_member.id
        appointment_data["hospital"] = hospital.id
        appointment_data["appointment_identifier"] = appointment_identifier
        appointment_data["doctor"] = doctor.id
        appointment_data["department"] = department.id
        appointment_data["uhid"] = uhid
        appointment_data["status"] = 1
        if data["status"] == "Cancelled":
            appointment_data["status"] = 2
        appointment_data["payment_status"] = None
        if data["payment_status"] == "Paid":
            appointment_data["payment_status"] = "success"
        if data.get("appointmentMode"):
            appointment_data["appointment_mode"] = data.get("appointmentMode")
        appointment_data["episode_number"] = data.get("episodeNumber", None)
        try:
            datetime_object = datetime.strptime(
                data["appointmentDatetime"], '%Y%m%d%H%M%S')
            appointment_data["appointment_date"] = datetime_object.date()
            appointment_data["appointment_slot"] = datetime_object.time().strftime(
                "%H:%M:%S %p")
            appointment_instance = Appointment.objects.filter(
                appointment_identifier=appointment_identifier).first()
            if appointment_instance:
                appointment_serializer = AppointmentSerializer(
                    appointment_instance, data=appointment_data, partial=True)
            else:
                appointment_data["booked_via_app"] = False
                appointment_serializer = AppointmentSerializer(
                    data=appointment_data)
            message = "Record Inserted"
            appointment_serializer.is_valid(raise_exception=True)
            appointment_serializer.save()
        except Exception as e:
            message = "Field is Missing " + str(e)
        return Response({"message": message}, status=status.HTTP_200_OK)


class UpcomingAppointmentsAPIView(custom_viewsets.ReadOnlyModelViewSet):
    search_fields = ['patient__first_name', 'doctor__name', 'family_member__first_name',
                     'appointment_identifier', 'patient__uhid_number', 'family_member__uhid_number',
                     'patient__mobile', 'patient__email']
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsManipalAdminUser | IsSelfUserOrFamilyMember]
    ordering = ('-appointment_date', '-appointment_slot', 'status')
    list_success_message = 'Appointment list returned successfully!'
    retrieve_success_message = 'Appointment information returned successfully!'

    def get_queryset(self):
        patient = Patient.objects.filter(id=self.request.user.id).first()
        patient_appointment = super().get_queryset().filter(
            appointment_date__gte=datetime.now().date(), status=1).filter(
                (Q(uhid=patient.uhid_number) & Q(uhid__isnull=False)) | (Q(patient_id=patient.id) & Q(family_member__isnull=True)) | (Q(family_member_id__uhid_number__isnull=False) & Q(family_member_id__uhid_number=patient.patient.uhid_number)))
        family_members = patient.patient_family_member_info.all()
        for member in family_members:
            family_appointment = super().get_queryset().filter(
                appointment_date__gte=datetime.now().date(), status=1).filter(
                    Q(family_member_id=member.id) | (Q(patient_id__uhid_number__isnull=False) & Q(patient_id__uhid_number=member.uhid_number)) | (Q(uhid__isnull=False) & Q(uhid=member.uhid_number)) | (Q(family_member_id__uhid_number__isnull=False) & Q(family_member_id__uhid_number=member.uhid_number)))
            patient_appointment = patient_appointment.union(family_appointment)
        return patient_appointment


class CancelHealthPackageAppointment(ProxyView):
    source = 'cancelAppointment'
    permission_classes = [IsPatientUser | IsManipalAdminUser | InternalAPICall]

    def get_request_data(self, request):
        data = request.data
        appointment_id = data.get("appointment_identifier")
        reason_id = data.pop("reason_id")
        instance = HealthPackageAppointment.objects.filter(
            appointment_identifier=appointment_id).first()
        if not instance:
            raise AppointmentDoesNotExistsValidationException
        request.data["location_code"] = instance.hospital.code
        other_reason = data.pop("other", None)
        cancel_appointment = serializable_CancelAppointmentRequest(
            **request.data)
        request_data = custom_serializer().serialize(cancel_appointment, 'XML')
        data["reason_id"] = reason_id
        data["other_reason"] = other_reason
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        appointment_id = self.request.data.get("appointment_identifier")
        response_message = "We are unable to cancel the appointment. Please Try again"
        success_status = False
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            status = root.find("Status").text
            message = root.find("Message").text
            response_message = status
            if status == "SUCCESS":
                instance = HealthPackageAppointment.objects.filter(
                    appointment_identifier=appointment_id).first()
                if not instance:
                    raise AppointmentDoesNotExistsValidationException
                instance.appointment_status = "Cancelled"
                instance.reason_id = self.request.data.get("reason_id")
                instance.other_reason = self.request.data.get("other_reason")
                instance.save()
                success_status = True
                param = {}
                param["app_id"] = instance.appointment_identifier
                param["cancel_remark"] = instance.reason.reason
                param["location_code"] = instance.hospital.code
                request_param = cancel_and_refund_parameters(param)
                response = CancelAndRefundView.as_view()(request_param)
            return self.custom_success_response(message=response_message,
                                                success=success_status, data=None)
        raise ValidationError(
            "Could not process your request. Please try again")


class CancelAndRefundView(ProxyView):
    permission_classes = [IsPatientUser | InternalAPICall]
    source = 'UpdateApp'

    def get_request_data(self, request):
        cancel_update = serializable_UpdateCancelAndRefund(request.data)
        request_data = custom_serializer().serialize(cancel_update, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        response_message = "Please try again"
        response_data = {}
        response_success = False
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            status = root.find("Status").text
            message = root.find("Message")
            updated_response = root.find("UpdateAppResp")
            return Response(data={"status": status, "message": message, "updated_response": updated_response})
        return Response(status=status.HTTP_200_OK)


class ReBookView(ProxyView):
    permission_classes = [IsPatientUser | InternalAPICall]
    source = 'RebookApp'

    def get_request_data(self, request):
        cancel_update = serializable_UpdateRebookStatus(request.data)
        request_data = custom_serializer().serialize(cancel_update, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            status = root.find("Status").text
            message = root.find("Message")
            rebook_app_response = root.find("RebookAppResp")
            return Response(data={"status": status, "message": message, "rebook_app_response": rebook_app_response})
        return Response(status=status.HTTP_200_OK)


class ReBookDoctorAppointment(ProxyView):
    permission_classes = [IsPatientUser | InternalAPICall]
    source = 'bookAppointment'

    def get_request_data(self, request):
        instance_id = request.data.pop("instance")
        rescheduled = request.data.pop("rescheduled")
        slot_book = serializable_BookMySlot(request.data)
        request_data = custom_serializer().serialize(slot_book, 'XML')
        request.data["instance"] = instance_id
        request.data["rescheduled"] = rescheduled
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        response_message = "Unable to Book the Appointment. Please try again"
        response_data = {}
        response_success = False
        instance = Appointment.objects.filter(
            id=self.request.data["instance"]).first()
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            appointment_identifier = root.find("appointmentIdentifier").text
            status = root.find("Status").text
            if status == "FAILED":
                response_message = root.find("Message").text
            else:
                new_appointment = dict()
                appointment_date_time = self.request.data.get(
                    "appointment_date_time")
                datetime_object = datetime.strptime(
                    appointment_date_time, '%Y%m%d%H%M%S')
                time = datetime_object.time()
                new_appointment["appointment_date"] = datetime_object.date()
                new_appointment["appointment_slot"] = time.strftime(
                    "%H:%M:%S %p")
                new_appointment["status"] = 1
                new_appointment["appointment_identifier"] = appointment_identifier
                new_appointment["patient"] = instance.patient.id
                new_appointment["uhid"] = self.request.data.get("mrn")
                new_appointment["department"] = instance.department.id
                new_appointment["consultation_amount"] = instance.consultation_amount
                new_appointment["payment_status"] = instance.payment_status
                if instance.family_member:
                    new_appointment["family_member"] = instance.family_member.id
                new_appointment["doctor"] = instance.doctor.id
                new_appointment["hospital"] = instance.hospital.id
                appointment = AppointmentSerializer(data=new_appointment)
                appointment.is_valid(raise_exception=True)
                appointment = appointment.save()
                if instance.payment_appointment.exists():
                    payment_instance = instance.payment_appointment.filter(
                        status="success").first()
                    if payment_instance:
                        payment_instance.appointment = appointment
                        payment_instance.save()
                response_success = True
                response_message = "Appointment has been Rebooked"
                response_data["appointment_identifier"] = appointment_identifier
                return self.custom_success_response(message=response_message,
                                                    success=response_success, data=response_data)
        if not self.request.data["rescheduled"]:
            return self.custom_success_response(message=response_message,
                                                success=response_success, data=response_data)
        raise ValidationError(response_message)


class DoctorRescheduleAppointmentView(ProxyView):
    permission_classes = [IsPatientUser | InternalAPICall]
    source = 'ReScheduleApp'

    def get_request_data(self, request):
        reason_id = request.data.pop("reason_id")
        instance = Appointment.objects.filter(
            appointment_identifier=self.request.data["app_id"]).first()
        if not instance:
            raise ValidationError("Appointment doesn't Exist")
        other_reason = request.data.pop("other")
        slot_book = serializable_RescheduleAppointment(**request.data)
        request_data = custom_serializer().serialize(slot_book, 'XML')
        request.data["reason_id"] = reason_id
        request.data["other_reason"] = other_reason
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        response_message = "Unable to Book the Reschedule Appointment. Please try again"
        response_data = {}
        response_success = False
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            status = root.find("Status").text
            if status == "1":
                reschedule_response = root.find("ReScheduleAppResp").text
                if reschedule_response:
                    new_appointment_response = ast.literal_eval(
                        reschedule_response)[0]
                    message = new_appointment_response["Message"]
                    response_message = message
                    if message == "Appointment Rescheduled Successfully":
                        new_appointment = dict()
                        appointment_id = new_appointment_response["NewApptId"]
                        instance = Appointment.objects.filter(
                            appointment_identifier=self.request.data["app_id"]).first()
                        appointment_date_time = self.request.data.get(
                            "new_date")
                        datetime_object = datetime.strptime(
                            appointment_date_time, '%Y%m%d%H%M%S')
                        time = datetime_object.time()
                        new_appointment["appointment_date"] = datetime_object.date(
                        )
                        new_appointment["appointment_slot"] = time.strftime(
                            "%H:%M:%S %p")
                        new_appointment["status"] = 1
                        new_appointment["appointment_identifier"] = appointment_id
                        new_appointment["patient"] = instance.patient.id
                        new_appointment["uhid"] = instance.uhid
                        new_appointment["department"] = instance.department.id
                        new_appointment["consultation_amount"] = instance.consultation_amount
                        new_appointment["payment_status"] = instance.payment_status
                        if instance.family_member:
                            new_appointment["family_member"] = instance.family_member.id
                        new_appointment["doctor"] = instance.doctor.id
                        new_appointment["hospital"] = instance.hospital.id
                        new_appointment["appointment_mode"] = self.request.data.get(
                            "app_type")
                        appointment = AppointmentSerializer(
                            data=new_appointment)
                        appointment.is_valid(raise_exception=True)
                        appointment = appointment.save()
                        if instance.payment_appointment.exists():
                            payment_instance = instance.payment_appointment.filter(
                                status="success").first()
                            if payment_instance:
                                payment_instance.appointment = appointment
                                payment_instance.save()
                        instance.status = 5
                        instance.reason_id = self.request.data.get("reason_id")
                        instance.other_reason = self.request.data.get(
                            "other_reason")
                        instance.save()
                        response_success = True
                        response_message = "Appointment has been Rescheduled"
                        response_data["appointment_identifier"] = appointment_id
                        return self.custom_success_response(message=response_message,
                                                            success=response_success, data=response_data)
        raise ValidationError(response_message)


class DoctorsAppointmentAPIView(custom_viewsets.ReadOnlyModelViewSet):
    queryset = Appointment.objects.all()
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    permission_classes = [IsDoctor, ]
    serializer_class = AppointmentSerializer
    ordering = ('appointment_date', 'appointment_slot')
    filter_fields = ('appointment_date',
                     'appointment_identifier', 'vc_appointment_status',)
    list_success_message = 'Appointment list returned successfully!'
    retrieve_success_message = 'Appointment information returned successfully!'

    def get_queryset(self):
        qs = super().get_queryset()
        doctor_id = self.request.user.id
        doctor = Doctor.objects.filter(id=doctor_id).first()
        if not doctor:
            raise ValidationError("Doctor does not Exist")
        if self.request.query_params.get("hospital_visit", None):
            return qs.filter(
                doctor__code=doctor.code, status="1", appointment_mode="HV")

        if self.request.query_params.get("vc_appointment_status", None):
            return qs.filter(
                doctor__code=doctor.code, status="1", appointment_mode="VC", payment_status="success")
        return qs.filter(
            doctor__code=doctor.code, status="1", appointment_mode="VC", payment_status="success").exclude(
                vc_appointment_status=4)

    def list(self, request, *args, **kwargs):
        pagination_data = None
        doctor_id = self.request.user.id
        doctor = Doctor.objects.filter(id=doctor_id).first()
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            pagination_data = self.get_paginated_response(None)
        else:
            serializer = self.get_serializer(queryset, many=True)

        count_detail = dict()
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        if self.request.query_params.get("hospital_visit", None):
            count_detail["total"] = Appointment.objects.filter(
                doctor__code=doctor.code, status="1", appointment_mode="HV").count()
            count_detail["today"] = Appointment.objects.filter(
                doctor__code=doctor.code, status="1", appointment_mode="HV",
                appointment_date=today).count()
            count_detail["tomorrow"] = Appointment.objects.filter(
                doctor__code=doctor.code, status="1", appointment_mode="HV",
                appointment_date=tomorrow).count()
        else:
            count_detail["completed_count"] = Appointment.objects.filter(
                doctor__code=doctor.code, status="1", appointment_mode="VC", payment_status="success", vc_appointment_status=4).count()
            count_detail["today"] = Appointment.objects.filter(
                doctor__code=doctor.code, status="1", appointment_mode="VC", payment_status="success", appointment_date=today).exclude(
                vc_appointment_status=4).count()
            count_detail["tomorrow"] = Appointment.objects.filter(
                doctor__code=doctor.code, status="1", appointment_mode="VC", payment_status="success", appointment_date=tomorrow).exclude(
                vc_appointment_status=4).count()

        data = {
            "data": serializer.data,
            "message": self.list_success_message,
            "pagination_data": pagination_data,
            "count_details": count_detail
        }
        return Response(data, status=status.HTTP_200_OK)


class AppointmentDocumentsViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [AllowAny, ]
    model = AppointmentDocuments
    queryset = AppointmentDocuments.objects.all().order_by('-created_at')
    serializer_class = AppointmentDocumentsSerializer
    create_success_message = "Document is uploaded successfully."
    list_success_message = 'Documents returned successfully!'
    retrieve_success_message = 'Document information returned successfully!'
    update_success_message = 'Document information is updated successfuly!'
    delete_success_message = 'Your document is deleted successfuly!'
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, )
    search_fields = ['name', 'description']

    def get_permissions(self):
        if self.action in ['list', 'create', ]:
            permission_classes = [IsPatientUser]
            return [permission() for permission in permission_classes]

        if self.action in ['partial_update', 'retrieve', 'destroy']:
            permission_classes = [IsPatientUser, IsSelfDocument]
            return [permission() for permission in permission_classes]

        if self.action == 'update':
            permission_classes = [BlacklistUpdateMethodPermission]
            return [permission() for permission in permission_classes]

        return super().get_permissions()

    def create(self, request):
        appointment_instance = Appointment.objects.filter(
            appointment_identifier=request.data.get("appointment_identifier")).first()
        if not appointment_instance:
            raise ValidationError("Appointment doesn't Exist")
        if (request.data.get("name") and request.data.get("document_type")):
            name_list = request.data.get("name").split(",")
            document_type_list = request.data.get("document_type").split(",")
            if not (name_list and document_type_list) or not (len(name_list) == len(document_type_list)):
                raise ValidationError("Document parameter is missing")
        for i, f in enumerate(request.FILES.getlist('document')):
            document_param = dict()
            document_param["appointment_info"] = appointment_instance.id
            document_param["name"] = name_list[i]
            document_param["document"] = f
            document_param["document_type"] = document_type_list[i]
            document_serializer = self.serializer_class(data=document_param)
            document_serializer.is_valid(raise_exception=True)
            document_serializer.save()
        vital_param = dict()
        vital_param["blood_pressure"] = request.data.get(
            "blood_pressure", None)
        vital_param["body_temperature"] = request.data.get(
            "body_temperature", None)
        vital_param["weight"] = request.data.get("weight", None)
        vital_param["height"] = request.data.get("height", None)
        vital_param["appointment_info"] = appointment_instance.id
        appointment_vital_instance = AppointmentVital.objects.filter(
            appointment_info_id=appointment_instance.id).first()
        if appointment_vital_instance:
            vital_serializer = AppointmentVitalSerializer(
                appointment_vital_instance, data=vital_param, partial=True)
        else:
            vital_serializer = AppointmentVitalSerializer(data=vital_param)
        vital_serializer.is_valid(raise_exception=True)
        vital_serializer.save()
        return Response(data={"message": "File Upload Sucessful"}, status=status.HTTP_200_OK)


class AppointmentVitalViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [AllowAny, ]
    model = AppointmentVital
    queryset = AppointmentVital.objects.all().order_by('-created_at')
    serializer_class = AppointmentVitalSerializer
    create_success_message = "Vitals are uploaded successfully."
    list_success_message = 'Vitals are returned successfully!'
    retrieve_success_message = 'Vitals are information returned successfully!'
    update_success_message = 'Vitals are information is updated successfuly!'
    delete_success_message = 'Vitals are document is deleted successfuly!'
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, )

    def get_permissions(self):
        if self.action in ['list', 'create', ]:
            permission_classes = [IsPatientUser]
            return [permission() for permission in permission_classes]

        if self.action in ['partial_update', 'retrieve', 'destroy']:
            permission_classes = [IsPatientUser, IsSelfDocument]
            return [permission() for permission in permission_classes]

        if self.action == 'update':
            permission_classes = [BlacklistUpdateMethodPermission]
            return [permission() for permission in permission_classes]

        return super().get_permissions()

    def create(self, request):
        appointment_instance = Appointment.objects.filter(
            appointment_identifier=request.data.pop("appointment_identifier")).first()
        if not appointment_instance:
            raise ValidationError("Appointment doesn't Exist")
        request.data["appointment_info"] = appointment_instance.id
        vital_serializer = self.serializer_class(data=request.data)
        vital_serializer.is_valid(raise_exception=True)
        vital_serializer.save()

        return Response(status=status.HTTP_200_OK)


class PrescriptionDocumentsViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [AllowAny, ]
    model = PrescriptionDocuments
    queryset = PrescriptionDocuments.objects.all().order_by('-created_at')
    serializer_class = PrescriptionDocumentsSerializer
    create_success_message = "Prescription Document is uploaded successfully."
    list_success_message = 'PrescriptionDocuments returned successfully!'
    retrieve_success_message = 'Prescription Documents information returned successfully!'
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, )

    def get_permissions(self):
        if self.action in ['list', 'create', ]:
            permission_classes = [IsPatientUser | IsDoctor]
            return [permission() for permission in permission_classes]

        if self.action in ['partial_update', 'retrieve', 'destroy', 'update']:
            permission_classes = [BlacklistUpdateMethodPermission]
            return [permission() for permission in permission_classes]

        return super().get_permissions()

    def get_queryset(self):
        queryset = super().get_queryset()
        uhid = self.request.query_params.get("uhid", None)
        if not uhid:
            raise ValidationError("Invalid Parameters")
        return queryset.filter(appointment_info__uhid=uhid)

    def create(self, request):
        document_param = dict()
        appointment_instance = Appointment.objects.filter(
            appointment_identifier=request.data.get("appointment_identifier")).first()
        if not appointment_instance:
            raise ValidationError("Appointment doesn't Exist")
        for i, f in enumerate(request.FILES.getlist('prescription')):
            document_param["appointment_info"] = appointment_instance.id
            document_param["prescription"] = f
            document_param["name"] = f.name
            document_param["appointment_identifier"] = appointment_instance.appointment_identifier
            document_param["episode_number"] = appointment_instance.episode_number
            document_param["hospital_code"] = appointment_instance.hospital.code
            document_param["department_code"] = appointment_instance.department.code
            document_param["episode_date_time"] = appointment_instance.episode_date_time
            document_serializer = self.serializer_class(data=document_param)
            document_serializer.is_valid(raise_exception=True)
            prescription = document_serializer.save()
            appointment_prescription = AppointmentPrescription.objects.filter(
                appointment_info=appointment_instance.id).first()
            if not appointment_prescription:
                data = dict()
                data["appointment_info"] = appointment_instance.id
                prescription_serializer = AppointmentPrescriptionSerializer(
                    data=data)
                prescription_serializer.is_valid(raise_exception=True)
                appointment_prescription = prescription_serializer.save()
            appointment_prescription.prescription_documents.add(prescription)
        return Response(data={"message": "File Upload Sucessful"}, status=status.HTTP_200_OK)


class ManipalPrescriptionViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [AllowAny, ]
    model = PrescriptionDocuments
    queryset = PrescriptionDocuments.objects.all().order_by('-created_at')
    serializer_class = PrescriptionDocumentsSerializer
    create_success_message = "Prescription Document is uploaded successfully."
    list_success_message = 'PrescriptionDocuments returned successfully!'
    retrieve_success_message = 'Prescription Documents information returned successfully!'
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, )

    def get_queryset(self):
        queryset = super().get_queryset()
        uhid = self.request.query_params.get("uhid", None)
        if not uhid:
            raise ValidationError("Invalid Parameters")
        return queryset.filter(appointment_info__uhid=uhid)

    def create(self, request):
        document_param = dict()
        appointment_identifier = request.query_params.get(
            "appointment_identifier")
        if not appointment_identifier:
            raise ValidationError("Paramter Missing")
        appointment_instance = Appointment.objects.filter(
            appointment_identifier=appointment_identifier).first()
        if not appointment_instance:
            raise ValidationError("Appointment doesn't Exist")
        for i, f in enumerate(request.FILES.getlist('prescription')):
            document_param["appointment_info"] = appointment_instance.id
            document_param["prescription"] = f
            document_param["name"] = f.name
            document_param["appointment_identifier"] = appointment_instance.appointment_identifier
            document_param["episode_number"] = appointment_instance.episode_number
            document_param["hospital_code"] = appointment_instance.hospital.code
            document_param["department_code"] = appointment_instance.department.code
            document_param["episode_date_time"] = appointment_instance.episode_date_time
            document_serializer = self.serializer_class(data=document_param)
            document_serializer.is_valid(raise_exception=True)
            prescription = document_serializer.save()
            appointment_prescription = AppointmentPrescription.objects.filter(
                appointment_info=appointment_instance.id).first()
            if not appointment_prescription:
                data = dict()
                data["appointment_info"] = appointment_instance.id
                prescription_serializer = AppointmentPrescriptionSerializer(
                    data=data)
                prescription_serializer.is_valid(raise_exception=True)
                appointment_prescription = prescription_serializer.save()
            appointment_prescription.prescription_documents.add(prescription)

        return Response(data={"message": "File Upload Sucessful"}, status=status.HTTP_200_OK)


class FeedbackViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [AllowAny, ]
    model = Feedbacks
    queryset = Feedbacks.objects.all().order_by('-created_at')
    serializer_class = FeedbacksSerializer
    create_success_message = "Feedback is uploaded successfully."
    list_success_message = 'Feedbacks returned successfully!'
    retrieve_success_message = 'Feedbacks information returned successfully!'
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, )

    def create(self, request):
        user_id = request.user.id
        patient = Patient.objects.filter(id=user_id).first()
        if not patient:
            raise ValidationError("Patient does not Exist")
        request.data["user_id"] = patient.id
        feedback_instance = Feedbacks.objects.filter(
            user_id__id=patient.id).first()
        request.data["user_id"] = patient.id
        if feedback_instance:
            feedback_serializer = FeedbacksSerializer(
                feedback_instance, data=request.data, partial=True)
        else:
            feedback_serializer = FeedbacksSerializer(data=request.data)
        feedback_serializer.is_valid(raise_exception=True)
        feedback_serializer.save()
        return Response(data={"message": "Feedback Submitted"}, status=status.HTTP_200_OK)


class CurrentPatientListView(ProxyView):
    permission_classes = [IsDoctor]
    source = 'CurrentPatients'

    def get_request_data(self, request):
        patient_list = serializable_CurrentPatientList(**request.data)
        request_data = custom_serializer().serialize(patient_list, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response.content)
        status = root.find("Status").text
        message = root.find("Message").text
        patient_list = []
        if status == '1':
            patient_list = ast.literal_eval(root.find("PatientList").text)
        return self.custom_success_response(message=message,
                                            success=True, data={"patient_list": patient_list})


class AppointmentPrescriptionViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [AllowAny, ]
    model = AppointmentPrescription
    queryset = AppointmentPrescription.objects.all().order_by('-created_at')
    serializer_class = AppointmentPrescriptionSerializer
    create_success_message = "Prescription Document is uploaded successfully."
    list_success_message = 'PrescriptionDocuments returned successfully!'
    retrieve_success_message = 'Prescription Documents information returned successfully!'
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, )

    def get_queryset(self):
        queryset = super().get_queryset()
        uhid = self.request.query_params.get("uhid", None)
        if not uhid:
            raise ValidationError("Invalid Parameters")
        return queryset.filter(appointment_info__uhid=uhid)
