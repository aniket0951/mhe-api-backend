import ast
import json
import xml.etree.ElementTree as ET
from datetime import datetime

import requests
from django.core import serializers
from django.db.models import Q
from django.forms.models import model_to_dict
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from apps.doctors.models import Doctor
from apps.doctors.serializers import (DepartmentSerializer,
                                      DepartmentSpecificSerializer,
                                      DoctorSerializer,
                                      HospitalDetailSerializer,
                                      HospitalSerializer)
from apps.master_data.models import Department, Hospital, Specialisation
from django_filters.rest_framework import DjangoFilterBackend
from proxy.custom_serializables import \
    SlotAvailability as serializable_SlotAvailability
from proxy.custom_serializers import ObjectSerializer as custom_serializer
from proxy.custom_views import ProxyView
from rest_framework import filters, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

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
class DoctorViewSet(ModelViewset):
    serializer_class = DoctorSerializer
    queryset = Doctor.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ['specialisations', 'linked_hospitals']

    def get_queryset(self):
        queryset = Doctor.objects.filter(specialisations__code = 'dmc' , linked_hospitals__code = 'whf')
        return queryset


"""


class DoctorsListView(generics.ListCreateAPIView):
    permission_classes = [AllowAny]
    search_fields = ['first_name',
                     'hospital_departments__department__name', 'code']
    filter_backends = (filters.SearchFilter,)
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer


class DoctorsAPIView(generics.ListCreateAPIView):
    permission_classes = [AllowAny]
    search_fields = ['first_name', 'hospital_departments__department__name']
    filter_backends = (filters.SearchFilter,)
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        location_id = self.request.query_params.get('location_id', None)
        date = self.request.query_params.get('date', None)
        qs = Doctor.objects.filter(hospital_departments__hospital__id=location_id).filter(
            Q(end_date__gte=date) | Q(end_date__isnull=True))
        return qs

    def list(self, request, *args, **kwargs):
        doctor = super().list(request, *args, **kwargs)
        if doctor.status_code == 200:
            doctors = {}
            doctors["doctors"] = doctor.data
            return Response({"data": doctors, "status": 200, "message": "List of all the doctors"})
        else:
            return Response({"status": doctor.code, "message": "No Doctor is Available"})


class LocationAPIView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = Hospital.objects.all()
    serializer_class = HospitalSerializer

    def list(self, request, *args, **kwargs):
        location = super().list(request, *args, **kwargs)
        if location.status_code == 200:
            locations = {}
            locations["locations"] = location.data
            return Response({"data": locations, "status": 200, "message": "List of all the locations"})
        else:
            return Response({"status": location.code, "message": "No Location is Available"})


class PreferredLocationView(APIView):
    permission_classes = [AllowAny]
    serializers_class = HospitalSerializer
    queryset = Hospital.objects.all()

    def get(request):
        hospital = HospitalSerializer.objects.all()
        serializer = HospitalSerializer(hospital)
        context = {'status': 200, 'data': serializer.data}
        return Response(context)


class DepartmentAPIView(generics.ListCreateAPIView):
    permission_classes = [AllowAny]
    queryset = Department.objects.all()
    serializer_class = DepartmentSpecificSerializer

    def list(self, request, *args, **kwargs):
        department = super().list(request, *args, **kwargs)
        if department.status_code == 200:
            departments = {}
            departments["departments"] = department.data
            return Response({"data": departments, "status": 200, "message": "List of all the Departments"})
        else:
            return Response({"status": department.code, "message": "No Department is Available"})


class DoctorSlotAvailability(ProxyView):
    sync_method = 'getDoctorPriceAndSchedule'

    def get_request_data(self, request):
        data = request.data
        doctor_id = data.get("doctor_id")
        date = data.get("date")
        hospital_id = data.get("hospital_id")
        department_id = data.get("specialisation_id")
        doctor = Doctor.objects.filter(id=doctor_id, hospital_departments__hospital__id=hospital_id, hospital_departments__department__id=department_id).filter(
            Q(end_date__gte=date) | Q(end_date__isnull=True))
        print(doctor)
        # TODO: Global custom exception handler needs to be implemented
        # if not doctor:
        #     self.custom_success_response(message='No Doctor is available',
        #                                         success=False, data=None)
        hospital = Hospital.objects.filter(id=hospital_id).first()
        department = Department.objects.filter(id=department_id).first()
        y, m, d = date.split("-")
        date = d + m + y
        slots = serializable_SlotAvailability(
            doctor_code=doctor[0].code, location_code=hospital.code, schedule_date=date, speciality_code=department.code)
        request_data = custom_serializer().serialize(slots, 'XML')
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
        root = ET.fromstring(response.content)
        slots = root.find("timeSlots").text
        price = root.find("price").text
        slot_list = []
        if slots:
            slot_list = ast.literal_eval(slots)
        morning_slot = []
        afternoon_slot = []
        evening_slot = []
        response = {}
        for slot in slot_list:
            if slot['startTime'][-2] == 'A':
                time = slot['startTime'][12:]
                morning_slot.append(time.strip())
            else:
                time = slot['startTime'][12:-3]
                date = datetime.strptime(time.strip(), '%H:%M:%S')
                time = slot['startTime'][13:]
                if (date.hour < 5) or (date.hour == 12):
                    afternoon_slot.append(time)
                else:
                    evening_slot.append(time)
        response["morning_slot"] = morning_slot
        response["afternoon_slot"] = afternoon_slot
        response["evening_slot"] = evening_slot
        response["price"] = price
        return self.custom_success_response(message='Available slots',
                                            success=True, data=response)


@api_view(['GET'])
@permission_classes([AllowAny])
def DoctorDetailView(request):
    data = request.query_params
    doctor_id = data.get("doctor_id")
    date = data.get("date")
    hospital_id = data.get("hospital_id")
    specialisation_id = data.get("specialisation_id")
    hospital = Hospital.objects.filter(id=hospital_id).first()
    specialisation = Specialisation.objects.filter(
        id=specialisation_id).first()
    doctor = Doctor.objects.filter(id=doctor_id, linked_hospitals__id=hospital_id, specialisations__id=specialisation_id).filter(
        Q(end_date__gte=date) | Q(end_date__isnull=True))
    if not doctor:
        return Response({"message": "Doctor is not available on this date", "status": 402})
    tmpJson = serializers.serialize("json", doctor)
    tmpObj = json.loads(tmpJson)
    if(len(tmpObj) == 0):
        return Response({"message": "Doctor is not available on this date", "status": 400})
    json_to_be_returned = tmpObj[0]
    print(tmpObj[0]["fields"])
    y, m, d = date.split("-")
    date_concat = d + m + y
    date = date_concat
    doctor_code = doctor[0].code
    location_code = hospital.code
    speciality_code = specialisation.code
    url = "https://172.16.241.227:789/Common.svc/getDoctorPriceAndSchedule"
    payload = "<DoctorParam><doctorCode>{0}</doctorCode><locationCode>{1}</locationCode><scheduleDate>{2}</scheduleDate><visitType>Appiontment</visitType><appointmentType>New</appointmentType><reasonForVisitCode>CONSULT</reasonForVisitCode><specialtyCode>{3}</specialtyCode><mobileNo>1</mobileNo><pdiscountAmount>1</pdiscountAmount><promocode>AA</promocode></DoctorParam>".format(
        doctor_code, location_code, date, speciality_code)
    response = requests.request(
        "POST", url, data=payload, headers=headers, verify=False)
    root = ET.fromstring(response.content)
    print(response.content)
    slots = root.find("timeSlots")
    price = root.find("price").text
    slot_list = ast.literal_eval(slots.text)
    morning_slot = []
    afternoon_slot = []
    evening_slot = []
    for slot in slot_list:
        if slot['startTime'][-2] == 'A':
            time = slot['startTime'][13:]
            morning_slot.append(time)
        else:
            time = slot['startTime'][13:-3]
            date = datetime.strptime(time, '%H:%M:%S')
            time = slot['startTime'][13:]
            if (date.hour < 5) or (date.hour == 12):
                afternoon_slot.append(time)
            else:
                evening_slot.append(time)
    json_to_be_returned["morning_slot"] = morning_slot
    json_to_be_returned["afternoon_slot"] = afternoon_slot
    json_to_be_returned["evening_slot"] = evening_slot
    return Response({"data": json_to_be_returned, "message": "Available slot", "status": 200})
