import base64
import datetime
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime

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
from apps.users.models import BaseUser
from django_filters.rest_framework import DjangoFilterBackend
from proxy.custom_serializables import BookMySlot as serializable_BookMySlot
from proxy.custom_serializables import \
    CancelAppointmentRequest as serializable_CancelAppointmentRequest
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
from utils.custom_permissions import (InternalAPICall, IsManipalAdminUser,
                                      IsPatientUser, IsSelfUserOrFamilyMember,
                                      SelfUserAccess)
from utils.custom_sms import send_sms

from .exceptions import (AppointmentAlreadyExistsException,
                         AppointmentDoesNotExistsValidationException)
from .models import Appointment, CancellationReason, HealthPackageAppointment
from .serializers import (AppointmentSerializer, CancellationReasonSerializer,
                          HealthPackageAppointmentSerializer)
from .utils import cancel_and_refund_parameters, rebook_parameters


class AppointmentsAPIView(custom_viewsets.ReadOnlyModelViewSet):
    search_fields = ['patient__first_name', 'doctor__name', 'family_member__first_name',
                     'appointment_identifier', 'patient__uhid_number', 'family_member__uhid_number',
                     'patient__mobile', 'patient__email']
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsManipalAdminUser | IsSelfUserOrFamilyMember]
    ordering = ('-appointment_date', '-appointment_slot', 'status')
    create_success_message = None
    list_success_message = 'Appointment list returned successfully!'
    retrieve_success_message = 'Appointment information returned successfully!'
    update_success_message = None

    def get_queryset(self):
        family_member = self.request.query_params.get("user_id", None)
        is_upcoming = self.request.query_params.get("is_upcoming", False)
        is_cancelled = self.request.query_params.get("is_cancelled", False)
        if ManipalAdmin.objects.filter(id=self.request.user.id).exists():
            if is_cancelled == "true":
                return super().get_queryset().filter(status=2)
            if is_cancelled == "false":
                return super().get_queryset().filter(appointment_date__gte=datetime.now().date(), status=1)
            return super().get_queryset()

        elif (family_member is not None):
            member = FamilyMember.objects.filter(id=family_member).first()
            if not member:
                raise PatientDoesNotExistsValidationException
            if is_upcoming:
                return super().get_queryset().filter(appointment_date__gte=datetime.now().date(), status=1).filter(Q(family_member_id=family_member) | (Q(patient_id__uhid_number__isnull=False) & Q(patient_id__uhid_number=member.uhid_number) & Q(family_member__isnull=True)) | (Q(uhid__isnull=False) & Q(uhid=member.uhid_number)) | (Q(family_member_id__uhid_number__isnull=False) & Q(family_member_id__uhid_number=member.uhid_number)))
            return super().get_queryset().filter((Q(family_member_id__uhid_number__isnull=False) & Q(family_member_id__uhid_number=member.uhid_number)) | Q(family_member_id=family_member) | (Q(patient_id__uhid_number__isnull=False) & Q(patient_id__uhid_number=member.uhid_number) & Q(family_member__isnull=True)) | (Q(uhid__isnull=False) & Q(uhid=member.uhid_number))).filter(Q(appointment_date__lt=datetime.now().date()) | Q(status=2))
        else:
            patient = Patient.objects.filter(id=self.request.user.id).first()
            if is_upcoming:
                return super().get_queryset().filter(appointment_date__gte=datetime.now().date(), status=1).filter((Q(uhid=patient.uhid_number) & Q(uhid__isnull=False)) | (Q(patient_id=patient.id) & Q(family_member__isnull=True)) | (Q(family_member_id__uhid_number__isnull=False) & Q(family_member_id__uhid_number=patient.patient.uhid_number)))
            return super().get_queryset().filter((Q(uhid=patient.uhid_number) & Q(uhid__isnull=False)) | (Q(patient_id=patient.id) & Q(family_member__isnull=True)) | (Q(family_member_id__uhid_number__isnull=False) & Q(family_member_id__uhid_number=patient.patient.uhid_number))).filter(Q(appointment_date__lt=datetime.now().date()) | Q(status=2))


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
                appointment = AppointmentSerializer(data=new_appointment)
                appointment.is_valid(raise_exception=True)
                appointment.save()
                appointment_data = appointment.data
                if appointment_data["family_member"]:
                    user_message = "Dear {0}, Your Appointment has been booked by {6} with {1} on {2} at {3} with appointment id:{4} at {5}".format(appointment_data["family_member"]["first_name"], appointment_data["doctor"][
                                                                                                                                                    "name"], appointment_data["appointment_date"], appointment_data["appointment_slot"], appointment_data["appointment_identifier"], appointment_data["hospital"]["address"], appointment_data["patient"]["first_name"])
                    if str(appointment_data["family_member"]["mobile"]) == str(appointment_data["patient"]["mobile"]):
                        send_sms(mobile_number=str(
                            appointment_data["family_member"]["mobile"]), message=user_message)
                    else:
                        send_sms(mobile_number=str(
                            appointment_data["patient"]["mobile"]), message=user_message)
                        send_sms(mobile_number=str(
                            appointment_data["family_member"]["mobile"]), message=user_message)
                else:
                    user_message = "Dear {0}, Your Appointment has been booked with {1} on {2} at {3} with appointment id:{4} at {5}".format(
                        appointment_data["patient"]["first_name"], appointment_data["doctor"]["name"], appointment_data["appointment_date"], appointment_data["appointment_slot"], appointment_data["appointment_identifier"], appointment_data["hospital"]["address"])
                    send_sms(mobile_number=str(
                        appointment_data["patient"]["mobile"]), message=user_message)
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
        status = data.pop("status",None)
        instance = Appointment.objects.filter(
            appointment_identifier=appointment_id).first()
        if not instance:
            raise AppointmentDoesNotExistsValidationException
        request.data["location_code"] = instance.hospital.code
        cancel_appointment = serializable_CancelAppointmentRequest(
            **request.data)
        request_data = custom_serializer().serialize(cancel_appointment, 'XML')
        data["reason_id"] = reason_id
        data["status"] = status
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
                instance.save()
                success_status = True
                param = dict()
                param["app_id"] = instance.appointment_identifier
                param["cancel_remark"] = instance.reason.reason
                param["location_code"] = instance.hospital.code

                if instance.family_member:
                    user_message = "Dear {0}, Your Appointment with {1} on {2} at {3} with appointment id:{4} has been cancelled by {5}".format(instance.family_member.first_name,
                                                                                                                                                instance.doctor.name, instance.appointment_date, instance.appointment_slot, instance.appointment_identifier, instance.patient.first_name)
                    if str(instance.family_member.mobile) == str(instance.patient.mobile):
                        send_sms(mobile_number=str(
                            instance.patient.mobile.raw_input), message=user_message)
                    else:
                        send_sms(mobile_number=str(
                            instance.patient.mobile.raw_input), message=user_message)
                        send_sms(mobile_number=str(
                            instance.family_member.mobile.raw_input), message=user_message)
                else:
                    user_message = "Dear {0}, Your Appointment with {1} on {2} at {3} with appointment id:{4} has been cancelled as per your request".format(instance.patient.first_name,
                                                                                                                                                             instance.doctor.name, instance.appointment_date, instance.appointment_slot, instance.appointment_identifier)
                    send_sms(mobile_number=str(
                        instance.patient.mobile.raw_input), message=user_message)
                request_param = cancel_and_refund_parameters(param)
                response = CancelAndRefundView.as_view()(request_param)
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
        return queryset.filter(patient_id=self.request.user.id, hospital_id=self.request.query_params.get("location_id", None)).distinct('doctor')


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
                    if instance.family_member:
                        user_message = "Hi {0},Your Health package appointment has been rebooked on {1} at {2}".format(instance.family_member.first_name, instance.appointment_date.date(),
                                                                                                                       instance.appointment_date.time())
                        send_sms(mobile_number=str(
                            instance.family_member.mobile.raw_input), message=user_message)
                    user_message = "Hi {0},Your Health package appointment has been rebooked on {1} at {2}".format(instance.patient.first_name, instance.appointment_date.date(),
                                                                                                                   instance.appointment_date.time())
                    send_sms(mobile_number=str(
                        instance.patient.mobile.raw_input), message=user_message)
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
        required_keys = ['UHID', 'doctorCode', 'appointmentIdentifier', 'appointmentDatetime',
                         'locationCode', 'status']
        data = request.data
        appointment_data = dict()
        if not data and set(required_keys).issubset(set(data.keys())):
            raise ValidationError("Appointment attribute is missing")
        uhid = data["UHID"]
        patient = Patient.objects.filter(uhid_number=uhid).first()
        family_member = FamilyMember.objects.filter(uhid_number=uhid).first()
        doctor = Doctor.objects.filter(code=data["doctorCode"].upper()).first()
        hospital = Hospital.objects.filter(code=data["locationCode"]).first()
        if not (patient or family_member):
            return Response({"message": "User is not App user"}, status=status.HTTP_200_OK)
        if not (doctor and hospital):
            return Response({"message": "Hospital or doctor is not available"}, status=status.HTTP_200_OK)
        appointment_data["booked_via_app"] = False
        datetime_object = datetime.strptime(
            data["appointmentDatetime"], '%Y%m%d%H%M%S')
        time = datetime_object.time()
        appointment_data["patient"] = patient
        appointment_data["family_member"] = family_member
        appointment_data["appointment_date"] = datetime_object.date()
        appointment_data["appointment_slot"] = time.strftime("%H:%M:%S %p")
        appointment_data["hospital"] = hospital.id
        appointment_data["appointment_identifier"] = data["appointmentIdentifier"]
        appointment_data["doctor"] = doctor.id
        appointment_data["uhid"] = uhid
        appointment_data["status"] = 1
        if data["status"] == "Cancelled":
            appointment_data["status"] = 2
        appointment_serializer = AppointmentSerializer(data=appointment_data)
        appointment_serializer.is_valid(raise_exception=True)
        appointment_serializer.save()
        return Response(data=appointment_serializer.data, status=status.HTTP_200_OK)


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
        cancel_appointment = serializable_CancelAppointmentRequest(
            **request.data)
        request_data = custom_serializer().serialize(cancel_appointment, 'XML')
        data["reason_id"] = reason_id
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
                    payment_instance = instance.payment_appointment.get()
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


class RescheduleAppointmentView(APIView):

    def post(self, request, format=None):
        param = {}
        param["appointment_identifier"] = request.data.get(
            "appointment_identifier")
        param["reason_id"] = request.data.get("reason_id")
        param["status"] = 5
        if not (param["appointment_identifier"] and param["reason_id"]):
            raise ValidationError("Appointment id or Reason is missing")
        appointment = Appointment.objects.filter(
                appointment_identifier=request.data.get("appointment_identifier")).first()
        if not appointment:
                raise ValidationError("Appointment does not Exist")
        new_date = request.data.get("appointment_date_time")
        request_param = doctor_rebook_parameters(appointment, new_date)
        response = ReBookDoctorAppointment.as_view()(request_param)
        if response.status_code == 200 and response.data["success"]:
            request_param = cancel_parameters(param)
            response_cancel = CancelMyAppointment.as_view()(request_param)
            return Response({"message": response.data["message"],
                                 "success": response.data["success"], "data": response.data["data"]})
        raise ValidationError(str(response.data["errors"][0]["message"]))
