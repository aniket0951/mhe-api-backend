import base64
import datetime
import hashlib
import xml.etree.ElementTree as ET

import requests
from django.shortcuts import render

import rest_framework
from apps.doctors.models import Doctor
from apps.master_data.models import Hospital, Specialisation
from apps.meta_app.permissions import Is_legit_user
from apps.patients.models import Patient
from apps.users.models import BaseUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Appointment
from .serializers import AppointmentDoctorSerializer, AppointmentSerializer

headers = {
    'Content-Type': "application/xml",
    'User-Agent': "PostmanRuntime/7.20.1",
    'Accept': "*/*",
    'Cache-Control': "no-cache",
    'Postman-Token': "c3ab8054-cca3-45d3-afe0-59936599cc57,211fe54d-707f-48b5-b6a4-8b953006078b",
    'Host': "172.16.241.227:789",
    'Accept-Encoding': "gzip, deflate",
    'Content-Length': "177",
    'Connection': "keep-alive",
    'cache-control': "no-cache"
}


"""
class AppointmentViewSet(viewsets.ModelViewSet):
    
    retrieve:
    Return the given Appointment.    
    
    list:
    Return a list of all the existing Appointments.    
    
    create:
    Create a new Appointment instance.
    
    queryset = Appointment.objects.all()
    serializer_class = Appointment
    filter_backends = (DjangoFilterBackend, OrderingFilter,)
    ordering_fields = '__all__'
     
    
    def get_serializer_class(self):
        
        Determins which serializer to user `list` or `detail`
        
        if self.action == 'retrieve':
            if hasattr(self , 'detail_serializer_class'):
                return self.detail_serializer_class
        return super().get_serializer_class()
    

    def get_queryset(self):
        
        Optionally restricts the returned queries by filtering against
        patient, hospital, Doctor  query parameter in the URL.
        
        queryset = Appointment.objects.all()
        patient = self.request.query_params.get('patient', None)
        hospital = self.request.query_params.get('hospital', None)
        doctor = self.request.query_params.get('doctor', None)
        if patient is not None:
            patient_name = patient.name
            queryset = queryset.filter(name = patient_name)
        if hospital is not None:
            hospital_name = hospital.description
            queryset = queryset.filter(description = hospital_name)
        if doctor is not None:
            doctor_name = doctor.name
            queryset = queryset.filter(name = doctor_name)
        return queryset
"""


class AppointmentsAPIView(generics.ListAPIView):
    search_fields = ['patient__first_name',
                     'doctor__first_name', 'hospital__profit_center']
    filter_backends = (filters.SearchFilter,)
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated, Is_legit_user]

    def get_queryset(self):

        queryset = Appointment.objects.all()
        patient_id = self.request.query_params.get('user_id', None)
        if patient_id is not None:
            queryset = queryset.filter(req_patient_id=patient_id)
            return queryset

    def list(self, request, *args, **kwargs):
        appointment = super().list(request, *args, **kwargs)
        if appointment.status_code == 200:
            appointments = {}
            appointments["appointments"] = appointment.data
            return Response({"data": appointments, "status": 200, "message": "List of all the doctors"})
        else:
            return Response({"status": appointment.code, "message": "No appointment is Available"})


@api_view(['POST'])
@permission_classes([IsAuthenticated, Is_legit_user])
def CreateAppointment(request):
    data = request.data
    patient_id = data.get("user_id")
    hospital_id = data.get("hospital_id")
    doctor_id = data.get("doctor_id")
    appointment_date = data.get("appointment_date")
    appointment_slot = data.get("appointment_slot")
    appointment_date_time = data.get("appointment_date_time")
    speciality_id = data.get("speciality_id")
    type = data.get("type")
    user = BaseUser.objects.filter(id=patient_id).first()
    speciality = Specialisation.objects.filter(id=speciality_id).first()
    hospital = Hospital.objects.filter(id=hospital_id).first()
    doctor = Doctor.objects.filter(id=doctor_id).first()
    """
    h, m , s = appointment_slot.split(":")
    appointment_slot = datetime.time(h,m,s)
    """
    y, m, d = appointment_date.split("-")
    date = y+m+d
    doctor_code = doctor.code
    appointment_date_time = appointment_date_time
    location_code = hospital.code
    name = user.first_name
    mobile = user.mobile
    email = user.email
    specialty_code = speciality.code
    type = type
    url = "https://localhost:8080/Common.svc/bookAppointment"
    payload = """<IbookAppointmentParam>
    <doctorCode>{0}</doctorCode>
    <appointmentDateTime>{1}</appointmentDateTime>
    <mrn></mrn>
    <locationCode>{2}</locationCode>
    <patientName>{3}</patientName>
    <mobile>{4}</mobile>
    <email>{5}</email>
    <duration>10</duration>
    <visitType>A</visitType>
    <appointmentType>{6}</appointmentType>
    <reasonForVisitCode>CONSULT</reasonForVisitCode>
    <chiefComplaint>NA</chiefComplaint>
    <fastCareID>PatientApp</fastCareID>
    <specialtyCode>{7}</specialtyCode>
    <title>Mr.</title>
</IbookAppointmentParam>""".format(doctor_code, appointment_date_time, location_code, name, mobile, email, type, specialty_code)
    response = requests.request(
        "POST", url, data=payload, headers=headers, verify=False)
    if response.status_code == 200:
        root = ET.fromstring(response.content)
        appointmentIdentifier = root.find("appointmentIdentifier").text
        status = root.find("Status").text
        if status == "FAILED":
            return Response({"message": "Unable to Book the Appointment. Please try again", "status": 403})
        else:
            appointment = Appointment(appointment_date=appointment_date, time_slot_from=appointment_slot,
                                      appointmentIdentifier=appointmentIdentifier, status=1, req_patient=user, doctor=doctor, hospital=hospital)
            appointment.save()
            return Response({"message": "Appointment has been created", "status": 200, "id": appointmentIdentifier})
    else:
        return Response({"message": "Unable to Book the Appointment. Please try again", "status": 403})


@api_view(['POST'])
@permission_classes([IsAuthenticated, Is_legit_user])
def CancelAppointment(request):
    data = request.data
    appointment_id = data.get("appointment_id")
    hospital_id = data.get("hospital_id")
    hospital = Hospital.objects.filter(id=hospital_id).first()
    instance = Appointment.objects.filter(
        appointmentIdentifier=appointment_id).first()
    location_code = hospital.code
    appointmentIdentifier = appointment_id
    payload = """
    <CancelAppointments>
    <appointmentIdentifier>{0}</appointmentIdentifier>
    <locationCode>{1}</locationCode>
    </CancelAppointments>""".format(appointmentIdentifier, location_code)
    print(payload)
    url = "https://172.16.241.227:789/Common.svc/cancelAppointment"
    response = requests.request(
        "POST", url, data=payload, headers=headers, verify=False)
    print(response.content)
    if response.status_code == 200:
        root = ET.fromstring(response.content)
        status = root.find("Status").text
        message = root.find("Message").text
        if status == "SUCCESS":
            instance.status = 2
            instance.save()
            return Response({"message": "Appointment has been cancelled", "status": 200})
        else:
            return Response({"message": "Couldn't Process the request. Please try again", "status": 403})


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
    token["response_url"] = ""
    token["return_url"] = ""
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
