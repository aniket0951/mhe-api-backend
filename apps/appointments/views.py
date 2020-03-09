import base64
import datetime
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime

import requests
import rest_framework
from django.conf import settings
from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.doctors.exceptions import DoctorDoesNotExistsValidationException
from apps.doctors.models import Doctor
from apps.manipal_admin.models import ManipalAdmin
from apps.master_data.exceptions import (
    DepartmentDoesNotExistsValidationException,
    HospitalDoesNotExistsValidationException)
from apps.master_data.models import Department, Hospital, Specialisation
from apps.patients.exceptions import PatientDoesNotExistsValidationException
from apps.patients.models import FamilyMember, Patient
from apps.users.models import BaseUser
from proxy.custom_serializables import BookMySlot as serializable_BookMySlot
from proxy.custom_serializables import \
    CancelAppointmentRequest as serializable_CancelAppointmentRequest
from proxy.custom_serializers import ObjectSerializer as custom_serializer
from proxy.custom_views import ProxyView
from utils import custom_viewsets
from utils.custom_permissions import (IsManipalAdminUser, IsPatientUser,
                                      IsSelfUserOrFamilyMember, SelfUserAccess)
from utils.custom_sms import send_sms

from .exceptions import AppointmentDoesNotExistsValidationException
from .models import Appointment, CancellationReason
from .serializers import (AppointmentSerializer, CancellationReasonSerializer,
                          DoctorAppointmentSerializer)


class AppointmentsAPIView(custom_viewsets.ReadOnlyModelViewSet):
    search_fields = ['patient__first_name',
                     'doctor__name', 'family_member__first_name']
    filter_backends = (filters.SearchFilter,)
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsManipalAdminUser | IsSelfUserOrFamilyMember]
    ordering_fields = ('-appointment_date', '-appointment_slot',)
    create_success_message = None
    list_success_message = 'Appointment list returned successfully!'
    retrieve_success_message = 'Appointment information returned successfully!'
    update_success_message = None

    def get_queryset(self):
        user = self.request.user.id
        family_member = self.request.query_params.get("user_id", None)
        if ManipalAdmin.objects.filter(id=self.request.user.id).exists():
            return super().get_queryset()
        elif (family_member is not None):
            return super().get_queryset().filter(family_member_id=family_member)
        else:
            return super().get_queryset().filter(patient_id=self.request.user.id)


class CreateMyAppointment(ProxyView):
    permission_classes = [IsSelfUserOrFamilyMember]
    source = 'bookAppointment'

    def get_request_data(self, request):

        patient_id = request.user.id
        family_member_id = request.data.pop("user_id", None)
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

        slot_book = serializable_BookMySlot(**request.data)
        request_data = custom_serializer().serialize(slot_book, 'XML')

        request.data["patient"] = patient
        request.data["family_member"] = family_member
        request.data["hospital"] = hospital
        request.data["doctor"] = doctor
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        response_message = "Unable to Book the Appointment. Please try again"
        response_data = {}
        response_success = False
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            appointmentIdentifier = root.find("appointmentIdentifier").text
            status = root.find("Status").text
            if status == "FAILED":
                message = root.find("Message").text
                return self.custom_success_response(message=message,
                                                    success=False, data=None)
            else:
                data = self.request.data
                family_member = data.get("family_member")
                new_appointment = {}
                appointment_date_time = data.pop("appointment_date_time")
                datetime_object = datetime.strptime(
                    appointment_date_time, '%Y%m%d%H%M%S')
                new_appointment["appointment_date"] = datetime_object.date()
                new_appointment["appointment_slot"] = datetime_object.time()
                new_appointment["status"] = 1
                new_appointment["appointment_identifier"] = appointmentIdentifier
                new_appointment["patient"] = data.get("patient").id
                if family_member:
                    new_appointment["family_member"] = family_member.id
                new_appointment["doctor"] = data.get("doctor").id
                new_appointment["hospital"] = data.get("hospital").id
                appointment = AppointmentSerializer(data=new_appointment)
                if not appointment.is_valid():
                    return self.custom_success_response(message=appointment.errors,
                                                        success=False, data=data)
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
                response_data["appointmentIdentifier"] = appointmentIdentifier

        return self.custom_success_response(message=response_message,
                                            success=response_success, data=response_data)


class CancelMyAppointment(ProxyView):
    source = 'cancelAppointment'
    permission_classes = [IsSelfUserOrFamilyMember]

    def get_request_data(self, request):
        data = request.data
        cancellation_reason = data.pop("reason_id")
        appointment_id = data.get("appointment_identifier")
        instance = Appointment.objects.filter(
            appointment_identifier=appointment_id).first()
        if not instance:
            raise AppointmentDoesNotExistsValidationException
        request.data["location_code"] = instance.hospital.code
        cancel_appointment = serializable_CancelAppointmentRequest(
            **request.data)
        request_data = custom_serializer().serialize(cancel_appointment, 'XML')
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
                instance.reason_id = self.request.data.get("reason")
                instance.save()
                success_status = True
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

        return self.custom_success_response(message=response_message,
                                            success=success_status, data=None)


class RecentlyVisitedDoctorlistView(custom_viewsets.ReadOnlyModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = DoctorAppointmentSerializer
    permission_classes = [IsPatientUser]
    create_success_message = None
    list_success_message = 'Appointment list returned successfully!'
    retrieve_success_message = 'Appointment information returned successfully!'
    update_success_message = None

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(patient_id=self.request.user.id).distinct('doctor')


class CancellationReasonlistView(custom_viewsets.ReadOnlyModelViewSet):
    queryset = CancellationReason.objects.all()
    serializer_class = CancellationReasonSerializer
    permission_classes = [AllowAny]

    list_success_message = 'Cancellation Reason list returned successfully!'
    retrieve_success_message = 'Cancellation Reason returned successfully!'
