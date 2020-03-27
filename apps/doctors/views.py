import ast
import json
import xml.etree.ElementTree as ET
from datetime import datetime

import requests
from django.core import serializers
from django.core.paginator import Paginator
from django.db.models import Q
from django.forms.models import model_to_dict
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.doctors.exceptions import DoctorDoesNotExistsValidationException
from apps.doctors.models import Doctor
from apps.doctors.serializers import (DepartmentSerializer,
                                      DepartmentSpecificSerializer,
                                      DoctorSerializer, HospitalSerializer)
from apps.manipal_admin.models import ManipalAdmin
from apps.master_data.models import Department, Hospital, Specialisation
from proxy.custom_serializables import \
    SlotAvailability as serializable_SlotAvailability
from proxy.custom_serializables import \
    DoctorSchedule as serializable_DoctorSchedule
from proxy.custom_serializers import ObjectSerializer as custom_serializer
from proxy.custom_views import ProxyView
from utils import custom_viewsets
from utils.custom_permissions import IsPatientUser
from utils.exceptions import InvalidRequest


class DoctorsAPIView(custom_viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    search_fields = ['name', 'hospital_departments__department__name', 'hospital__code', 'code']
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    ordering = ('name',)
    create_success_message = None
    list_success_message = 'Doctors list returned successfully!'
    retrieve_success_message = 'Doctors information returned successfully!'
    update_success_message = None

    def get_queryset(self):
        if ManipalAdmin.objects.filter(id=self.request.user.id).exists():
            return super().get_queryset()

        location_id = self.request.query_params.get('location_id', None)
        date = self.request.query_params.get('date', None)
        return Doctor.objects.filter(hospital_departments__hospital__id=location_id).filter(
            Q(end_date__gte=date) | Q(end_date__isnull=True))


class DoctorSlotAvailability(ProxyView):
    source = 'getDoctorPriceAndSchedule'
    permission_classes = [IsPatientUser]

    def get_request_data(self, request):
        data = request.data
        date = data.pop("date")
        try:
            doctor = Doctor.objects.filter(id=data.pop("doctor_id"), hospital_departments__hospital__id=data.get("hospital_id"), hospital_departments__department__id=data.get("department_id")).filter(
                Q(end_date__gte=date) | Q(end_date__isnull=True))
        except Exception as e:
            raise InvalidRequest

        if not doctor:
            raise DoctorDoesNotExistsValidationException
        hospital = Hospital.objects.filter(id=data.pop("hospital_id")).first()
        department = Department.objects.filter(
            id=data.pop("department_id")).first()
        y, m, d = date.split("-")
        data["schedule_date"] = d + m + y
        data["doctor_code"] = doctor[0].code
        data["location_code"] = hospital.code
        data["speciality_code"] = department.code

        slots = serializable_SlotAvailability(**request.data)
        request_data = custom_serializer().serialize(slots, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response.content)
        slots = root.find("timeSlots").text
        price = root.find("price").text
        morning_slot = []
        afternoon_slot = []
        evening_slot = []
        slot_list  = []
        if slots:
            slot_list = ast.literal_eval(slots)
        response = {}
        for slot in slot_list:
            time = datetime.strptime(
                slot['startTime'], '%d %b, %Y %I:%M:%S %p').time()
            if time.hour < 12:
                morning_slot.append(time.strftime("%H:%M:%S %p"))
            elif (time.hour >= 12) and (time.hour < 17):
                afternoon_slot.append(time.strftime("%I:%M:%S %p"))
            else:
                evening_slot.append(time.strftime("%I:%M:%S %p"))
        response["morning_slot"] = morning_slot
        response["afternoon_slot"] = afternoon_slot
        response["evening_slot"] = evening_slot
        response["price"] = price
        return self.custom_success_response(message='Available slots',
                                            success=True, data=response)

class DoctorScheduleView(ProxyView):
    source = 'weeklySchedule'
    permission_classes = [IsPatientUser]

    def get_request_data(self, request):
        data = request.data
        schedule = serializable_DoctorSchedule(**request.data)
        request_data = custom_serializer().serialize(schedule, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        data = {}
        root = ET.fromstring(response.content)
        schedule_lists = root.find("ScheduleList").text
        schedule_list = []
        records = {}
        if schedule_lists:
            schedule_list = ast.literal_eval(schedule_lists)
        for record in schedule_list:
            hospital = record["Hosp"]
            hospital_description = Hospital.objects.filter(code = hospital).first().description
            if hospital_description in records:
                records[hospital_description].append(record)
            else:
                records[hospital_description] =[]
                records[hospital_description].append(record)

        return self.custom_success_response(message='Available slots',
                                            success=True, data=records)
