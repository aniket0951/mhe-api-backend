from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.core import serializers
import json
import ast
from datetime import datetime
from django.db.models import Q
from django.forms.models import model_to_dict
from rest_framework.response import Response
from apps.doctors.models import Doctor
from apps.master_data.models import Hospital, Specialisation
from apps.doctors.serializers import DoctorSerializer, HospitalDetailSerializer, SpecialisationDetailSerializer,SpecialisationDetailSerializer,HospitalSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet
from rest_framework import generics
from rest_framework import filters
from rest_framework.views import APIView
import requests
import xml.etree.ElementTree as ET
import ast

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
    search_fields = ['specialisations__code', 'first_name', 'linked_hospitals__profit_center']
    filter_backends = (filters.SearchFilter,)
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer


class DoctorsAPIView(generics.ListCreateAPIView):
    
    search_fields = ['specialisations__code', 'first_name', 'linked_hospitals__profit_center']
    filter_backends = (filters.SearchFilter,)
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer

    
    def list(self, request, *args, **kwargs):
        location_id= self.request.query_params.get('location_id', None)
        date = self.request.query_params.get('date', None)
        queryset = Doctor.objects.filter(linked_hospitals__id = location_id).filter(Q(end_date__gte = date) | Q(end_date__isnull=True))
        serializer = self.get_serializer(queryset, many=True)
        doctors= {}
        doctors["doctor"] = serializer.data
        return Response({"data": doctors, "status": 200, "message":"List of all the doctors"})
    

class LocationAPIView(generics.ListAPIView):
    queryset          = Hospital.objects.all()
    serializer_class  = HospitalSerializer


    def list(self, request):
        queryset = Hospital.objects.all()
        serializer = HospitalSerializer(queryset, many=True)
        return Response({"data": serializer.data, "status" : 200})


class PreferredLocationView(APIView):
    serializers_class = HospitalSerializer
    queryset = Hospital.objects.all()

    def get(request):
        long = self.request.query_params.get('long', None)
        lat =  self.request.query_params.get('lat', None)
        hospital = HospitalSerializer.objects.all()
        serializer = HospitalSerializer(hospital)
        context = {'status' : 200, 'data':serializer.data}
        return Response(context) 



class SpecialisationAPIView(generics.ListCreateAPIView):
    queryset          = Specialisation.objects.all()
    serializer_class  = SpecialisationDetailSerializer

    def list(self, request):
        queryset = Specialisation.objects.all()
        serializer = SpecialisationDetailSerializer(queryset, many=True)
        return Response({"data": serializer.data, "status" : 200})


"""
class DoctorDetailAPIView(generics.RetrieveAPIView):
    
    queryset          = Doctor.objects.all()
    serializer_class  = DoctorDetailSerializer
    
    def get(self, request, pk, *args, **kwargs):
        doctor = Doctor.objects.get(pk=pk)
        serializer = SpecialisationDetailSerializer(doctor)
        return Response(serializer.data)
"""

@api_view(['GET'])
def DoctorDetailView(request):
    data = request.query_params
    doctor_id = data.get("doctor_id")
    date = data.get("date")
    hospital_id = data.get("hospital_id")
    specialisation_id = data.get("specialisation_id")
    hospital = Hospital.objects.filter(id = hospital_id).first()
    specialisation = Specialisation.objects.filter(id = specialisation_id).first()
    doctor = Doctor.objects.filter(id = doctor_id, linked_hospitals__id = hospital_id, specialisations__id = specialisation_id).filter(Q(end_date__gte = date) | Q(end_date__isnull=True))
    if not doctor:
        return Response({"message":"Doctor is not available on this date", "status": 402})
    tmpJson = serializers.serialize("json",doctor)
    tmpObj = json.loads(tmpJson)
    if(len(tmpObj) == 0):
        return Response({"message":"Doctor is not available on this date", "status" : 400})
    json_to_be_returned = tmpObj[0]
    print(tmpObj[0]["fields"])
    y, m , d = date.split("-")
    date_concat = d + m + y
    date = date_concat
    doctor_code = doctor[0].code
    location_code = hospital.code
    speciality_code = specialisation.code
    url = "https://localhost:8080/Common.svc/getDoctorPriceAndSchedule"
    payload = "<DoctorParam><doctorCode>{0}</doctorCode><locationCode>{1}</locationCode><scheduleDate>{2}</scheduleDate><visitType>Appiontment</visitType><appointmentType>New</appointmentType><reasonForVisitCode>CONSULT</reasonForVisitCode><specialtyCode>{3}</specialtyCode><mobileNo>1</mobileNo><pdiscountAmount>1</pdiscountAmount><promocode>AA</promocode></DoctorParam>".format(doctor_code, location_code,date, speciality_code)
    response = requests.request("POST", url, data=payload, headers=headers, verify = False)
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
    return Response({"data":json_to_be_returned, "message":"Available slot", "status": 200})



    

    
    
    



    
    
    
    

    
