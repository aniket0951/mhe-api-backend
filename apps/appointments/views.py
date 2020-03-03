import base64
import datetime
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime

import requests
from django.conf import settings
from django.shortcuts import render

import boto3
import rest_framework
from apps.doctors.models import Doctor
from apps.master_data.models import Department, Hospital, Specialisation
from apps.meta_app.permissions import IsLegitUser
from apps.patients.models import Patient, FamilyMember
from apps.users.models import BaseUser
from django_filters.rest_framework import DjangoFilterBackend
from proxy.custom_serializables import BookMySlot as serializable_BookMySlot
from proxy.custom_serializables import \
    CancelAppointmentRequest as serializable_CancelAppointmentRequest
from proxy.custom_serializers import ObjectSerializer as custom_serializer
from proxy.custom_views import ProxyView
from rest_framework import filters, generics, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from utils import custom_viewsets
from utils.custom_sms import send_sms
from utils.custom_permissions import IsPatientUser, SelfUserAccess, IsManipalAdminUser

from .exceptions import (AppointmentDoesNotExistsValidationException,
                         DepartmentDoesNotExistsValidationException,
                         DoctorDoesNotExistsValidationException,
                         HospitalDoesNotExistsValidationException,
                         PatientDoesNotExistsValidationException)
from .models import Appointment
from .serializers import AppointmentDoctorSerializer, AppointmentSerializer


class AppointmentsAPIView(custom_viewsets.ReadOnlyModelViewSet):
    search_fields = ['patient__first_name',
                     'doctor__first_name', 'family_member__first_name']
    filter_backends = (filters.SearchFilter,)
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsManipalAdminUser | IsLegitUser]

    create_success_message = None
    list_success_message = 'Appointment list returned successfully!'
    retrieve_success_message = 'Appointment information returned successfully!'
    update_success_message = None

    def get_queryset(self):
        user = self.request.user.id
        family_member = self.request.query_params.get("user_id", None)
        qs = super().get_queryset().order_by('-appointment_date', '-appointment_slot')

        if ManipalAdmin.objects.filter(id=request.user.id).exists():
            return qs
        elif (family_member is not None):
            return  qs.filter(family_member_id=family_member).order_by(
                '-appointment_date', '-appointment_slot')
        else:
            return qs.filter(patient_id= self.request.user.id).order_by(
                '-appointment_date', '-appointment_slot')


class CreateMyAppointment(ProxyView):
    permission_classes = [IsLegitUser]
    sync_method = 'bookAppointment'

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
        specialty = Department.objects.filter(
            id=request.data.pop("specialisation_id")).first()
        if not specialty:
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
        request.data['speciality_code'] = specialty.code

        slot_book = serializable_BookMySlot(**request.data)
        request_data = custom_serializer().serialize(slot_book, 'XML')

        request.data["patient"] = patient
        request.data["family_member"] = family_member
        request.data["hospital"] = hospital
        request.data["doctor"] = doctor
        return request_data

    def get_request_url(self, request):
        host = self.get_proxy_host()
        path = self.sync_method
        if path:
            return '/'.join([host, path])
        return host

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            print(response.content)
            appointmentIdentifier = root.find("appointmentIdentifier").text
            status = root.find("Status").text
            if status == "FAILED":
                message = root.find("Message").text
                return self.custom_success_response(message=message,
                                                    success=False, data=None)
            else:
                data = self.request.data
                new_appointment = {}
                appointment_date_time = data.pop("appointment_date_time")
                datetime_object = datetime.strptime(
                    appointment_date_time, '%Y%m%d%H%M%S')
                new_appointment["appointment_date"] = datetime_object.date()
                new_appointment["appointment_slot"] = datetime_object.time()
                new_appointment["status"] = 1
                new_appointment["patient"] = data.get("patient")
                new_appointment["family_member"] = data.get("family_member")
                new_appointment["appointmentIdentifier"] = appointmentIdentifier
                new_appointment["doctor"] = data.pop("doctor")
                new_appointment["hospital"] = data.pop("hospital")
                appointment = Appointment(**new_appointment)
                if not appointment:
                    raise AppointmentDoesNotExistsValidationException
                appointment.save()
                family_member = new_appointment["family_member"]
                patient = new_appointment["patient"]
                if family_member:
                    user_message = "Dear {0}, Your Appointment has been booked by {6} with {1} on {2} at {3} with appointment id:{4} at {5}".format(appointment.family_member.first_name,
                                                                                                                                                    appointment.doctor.name, appointment.appointment_date, appointment.appointment_slot, appointment.appointmentIdentifier, appointment.hospital.address, appointment.patient.first_name)
                    if str(family_member.mobile) == str(patient.mobile):
                        is_message_sent = send_sms(mobile_number=str(
                            appointment.patient.mobile.raw_input), message=user_message)
                    else:
                        send_sms(mobile_number=str(
                            appointment.patient.mobile.raw_input), message=user_message)
                        send_sms(mobile_number=str(
                            appointment.family_member.mobile.raw_input), message=user_message)
                else:
                    user_message = "Dear {0}, Your Appointment has been booked with {1} on {2} at {3} with appointment id:{4} at {5}".format(appointment.patient.first_name,
                                                                                                                                             appointment.doctor.name, appointment.appointment_date, appointment.appointment_slot, appointment.appointmentIdentifier, appointment.hospital.address)
                    send_sms(mobile_number=str(
                        appointment.patient.mobile.raw_input), message=user_message)
                message = "Appointment has been created"
                return self.custom_success_response(message=message,
                                                    success=True, data={"appointmentIdentifier": appointmentIdentifier})
        else:
            message = "Unable to Book the Appointment. Please try again"
            return self.custom_success_response(message=message,
                                                success=False, data=None)


class CancelMyAppointment(ProxyView):
    sync_method = 'cancelAppointment'
    permission_classes = [IsLegitUser]

    def get_request_data(self, request):
        data = request.data
        appointment_id = data.get("appointment_identifier")
        instance = Appointment.objects.filter(
            appointmentIdentifier=appointment_id).first()
        if not instance:
            raise AppointmentDoesNotExistsValidationException
        request.data["location_code"] = instance.hospital.code
        cancel_appointment = serializable_CancelAppointmentRequest(
            **request.data)
        request_data = custom_serializer().serialize(cancel_appointment, 'XML')
        return request_data

    def get_request_url(self, request):
        host = self.get_proxy_host()
        path = self.sync_method
        if path:
            return '/'.join([host, path])
        return host

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        appointment_id = self.request.data.get("appointment_identifier")
        root = ET.fromstring(response.content)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            status = root.find("Status").text
            message = root.find("Message").text
            if status == "SUCCESS":
                instance = Appointment.objects.filter(
                    appointmentIdentifier=appointment_id).first()
                if not instance:
                    raise AppointmentDoesNotExistsValidationException
                instance.status = 2
                instance.save()
                if instance.family_member:
                    user_message = "Dear {0}, Your Appointment with {1} on {2} at {3} with appointment id:{4} has been cancelled by {5}".format(instance.family_member.first_name,
                                                                                                                                                         instance.doctor.name, instance.appointment_date, instance.time_slot_from, instance.appointmentIdentifier, instance.patient.first_name)
                    if str(instance.family_member.mobile) == str(instance.patient.mobile):
                        send_sms(mobile_number=str(instance.patient.mobile.raw_input), message=user_message)
                    else:
                        send_sms(mobile_number=str(instance.patient.mobile.raw_input), message=user_message)
                        send_sms(mobile_number=str(instance.family_member.mobile.raw_input), message=user_message)
                else:
                    user_message = "Dear {0}, Your Appointment with {1} on {2} at {3} with appointment id:{4} has been cancelled as per your request".format(instance.patient.first_name,
                                                                                                                                                         instance.doctor.name, instance.appointment_date, instance.time_slot_from, instance.appointmentIdentifier)
                    send_sms(mobile_number=str(instance.patient.mobile.raw_input), message=user_message)
                return self.custom_success_response(message=status,
                                                    success=True, data=message)
            else:
                return self.custom_success_response(message=status,
                                                    success=False, data=message)
        else:
            return self.custom_success_response(message="We are unable to cancel the appointment. Please Try again",
                                                success=False, data=None)


class RecentlyVisitedDoctorlistView(custom_viewsets.ReadOnlyModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentDoctorSerializer
    permission_classes = [IsPatientUser]
    create_success_message = None
    list_success_message = 'Appointment list returned successfully!'
    retrieve_success_message = 'Appointment information returned successfully!'
    update_success_message = None

    def get_queryset(self):
        queryset = super().get_queryset()
        patient_id = self.request.user.id

        if patient_id is not None:
            return queryset.filter(patient_id=patient_id).distinct('doctor').order_by('-appointment_date')
        else:
            raise PatientDoesNotExistsValidationException


@api_view(['GET'])
@permission_classes([AllowAny])
def get_data(request):
    param = {}
    token = {}
    token["auth"] = {}
    token["auth"]["user"] = "manipalhospitaladmin"
    token["auth"]["key"] = "ldyVqN8Jr1GPfmwBflC2uQcKX2uflbRP"
    token["username"] = "Patient"
    token["accounts"] = []
    account = {
        "patient_name": "Jane Doe",
        "account_number": "ACC1",
        "amount": "150.25",
        "email": "abc@xyz.com",
        "phone": "9876543210"
    }
    token["accounts"].append(account)
    token["processing_id"] = "TESTAPPID819"
    token["paymode"] = None
    token["response_url"] = "https://www.google.com/"
    token["return_url"] = "https://www.google.com/"
    param["token"] = token
    param["check_sum_hash"] = get_checksum(
        token["auth"]["user"], token["auth"]["key"], token["processing_id"], "mid", "bDp0YXGlb0s4PEqdl2cEWhgGN0kFFEPD")
    param["mid"] = "ydLf7fPe"

    return Response(data=param)


def get_checksum(user, key, processing_id, mid, secret_key):
    hash_string = user + "|" + key + "|" + \
        processing_id + "|" + mid + "|" + secret_key
    checksum = base64.b64encode(hashlib.sha256(
        hash_string.encode("utf-8")).digest())
    return checksum
