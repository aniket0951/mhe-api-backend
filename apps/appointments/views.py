import base64
import datetime
import hashlib
import xml.etree.ElementTree as ET

import requests
from django.conf import settings
from django.shortcuts import render

import boto3
import rest_framework
from apps.doctors.models import Doctor
from apps.master_data.models import Department, Hospital, Specialisation
from apps.meta_app.permissions import Is_legit_user
from apps.patients.models import Patient
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

from .models import Appointment
from .serializers import AppointmentDoctorSerializer, AppointmentSerializer

AWS_ACCESS_KEY = settings.AWS_ACCESS_KEY
AWS_SECRET_ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY
REGION_NAME = settings.AWS_SNS_TOPIC_REGION
S3_BUCKET_NAME = settings.AWS_S3_BUCKET_NAME
S3_REGION_NAME = settings.AWS_S3_REGION_NAME


class AppointmentsAPIView(generics.ListAPIView):
    search_fields = ['req_patient__first_name',
                     'doctor__first_name']
    filter_backends = (filters.SearchFilter,)
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Appointment.objects.all()
        patient_id = self.request.query_params.get('user_id', None)
        if patient_id is not None:
            queryset = queryset.filter(
                req_patient_id=patient_id).order_by('-appointment_date')
            return queryset

    def list(self, request, *args, **kwargs):
        appointment = super().list(request, *args, **kwargs)
        if appointment.status_code == 200:
            appointments = {}
            appointments["appointments"] = appointment.data
            return Response({"data": appointments, "status": 200, "message": "List of all the doctors"})
        else:
            return Response({"status": appointment.code, "message": "No appointment is Available"})


class ShowAppointmentView(generics.ListAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [AllowAny]


class CreateMyAppointment(ProxyView):
    sync_method = 'bookAppointment'

    def get_request_data(self, request):
        data = request.data
        patient_id = data.get("user_id")
        hospital_id = data.get("hospital_id")
        doctor_id = data.get("doctor_id")
        appointment_date_time = data.get("appointment_date_time")
        speciality_id = data.get("specialisation_id")
        type = data.get("type")

        user = BaseUser.objects.filter(id=patient_id).first()
        speciality = Department.objects.filter(id=speciality_id).first()
        hospital = Hospital.objects.filter(id=hospital_id).first()
        doctor = Doctor.objects.filter(id=doctor_id).first()

        slot_book = serializable_BookMySlot(doctor_code=doctor.code, appointment_date_time=appointment_date_time,
                                            location_code=hospital.code, patient_name=user.first_name, mobile=str(
                                                user.mobile),
                                            email=str(user.email), speciality_code=speciality.code)
        request_data = custom_serializer().serialize(slot_book, 'XML')
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
                message = "Unable to Book the Appointment. Please try again"
                return self.custom_success_response(message=message,
                                                    success=False, data=None)
            else:
                data = self.request.data
                patient_id = data.get("user_id")
                hospital_id = data.get("hospital_id")
                doctor_id = data.get("doctor_id")
                appointment_date = data.get("date")
                appointment_slot = data.get("appointment_slot")
                appointmentIdentifier = appointmentIdentifier
                user = BaseUser.objects.filter(id=patient_id).first()
                hospital = Hospital.objects.filter(id=hospital_id).first()
                doctor = Doctor.objects.filter(id=doctor_id).first()
                appointment = Appointment(appointment_date=appointment_date, time_slot_from=appointment_slot,
                                          appointmentIdentifier=appointmentIdentifier, status=1, req_patient=user, doctor=doctor, hospital=hospital)
                appointment.save()
                user_message = "Dear {0}, Your Appointment has been booked with {1} on {2} at {3} with appointment id:{4}".format(user.first_name,
                                                                                                                                  doctor.first_name, appointment_date, appointment_slot, appointmentIdentifier)
                print(user_message)
                client = boto3.client("sns",
                                      aws_access_key_id=AWS_ACCESS_KEY,
                                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                                      region_name=REGION_NAME)
                """
                response = client.publish(PhoneNumber=str(user.mobile), Message=user_message, MessageAttributes={
                    'AWS.SNS.SMS.SMSType': {
                    'DataType': 'String',
                    'StringValue': 'Transactional'
                     }
                })
                """
                message = "Appointment has been created"
                return self.custom_success_response(message=message,
                                                    success=True, data={"appointmentIdentifier": appointmentIdentifier})
        else:
            message = "Unable to Book the Appointment. Please try again"
            return self.custom_success_response(message=message,
                                                success=False, data=None)


class CancelMyAppointment(ProxyView):
    sync_method = 'cancelAppointment'

    def get_request_data(self, request):
        data = request.data
        appointment_id = data.get("appointment_id")
        instance = Appointment.objects.filter(
            appointmentIdentifier=appointment_id).first()
        cancel_appointment = serializable_CancelAppointmentRequest(
            appointment_identifier=appointment_id, location_code=instance.hospital.code)
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
        appointment_id = self.request.data.get("appointment_id")
        root = ET.fromstring(response.content)
        print(response.content)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            status = root.find("Status").text
            message = root.find("Message").text
            if status == "SUCCESS":
                instance = Appointment.objects.filter(
                    appointmentIdentifier=appointment_id).first()
                instance.status = 2
                instance.save()
                return self.custom_success_response(message=status,
                                                    success=True, data=message)
            else:
                return self.custom_success_response(message=status,
                                                    success=False, data=message)


class RecentlyVisitedDoctorlistView(generics.ListAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentDoctorSerializer
    permission_classes = [IsAuthenticated, Is_legit_user]

    def get_queryset(self):
        queryset = Appointment.objects.all()
        patient_id = self.request.query_params.get('user_id', None)

        if patient_id is not None:
            queryset = queryset.filter(
                req_patient_id=patient_id).distinct('doctor')
            return queryset
        else:
            return Response({"message": "Patient does not exist", "status": 403})

    def list(self, request, *args, **kwargs):
        doctor = super().list(request, *args, **kwargs)
        if doctor.status_code == 200:
            doctors = {}
            doctors["doctors"] = doctor.data
            return Response({"data": doctors, "status": 200, "message": "List of all the doctors"})
        else:
            return Response({"status": doctor.code, "message": "No doctor is Available"})


@api_view(['GET'])
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
    token["paymode"] = ""
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
