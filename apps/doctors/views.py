import ast
import json
import xml.etree.ElementTree as ET

import requests
from django.core import serializers
from django.core.paginator import Paginator
from django.db.models import Q
from django.forms.models import model_to_dict
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.timezone import datetime
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.serializers import ValidationError
from django.contrib.auth.hashers import check_password
from rest_framework_jwt.utils import jwt_encode_handler, jwt_payload_handler
from rest_framework import status
from django.conf import settings

from apps.doctors.exceptions import DoctorDoesNotExistsValidationException
from apps.doctors.models import Doctor
from apps.doctors.serializers import (DepartmentSerializer,
                                      DepartmentSpecificSerializer,
                                      DoctorSerializer, HospitalSerializer)
from apps.manipal_admin.models import ManipalAdmin
from apps.master_data.models import Department, Hospital, Specialisation
from proxy.custom_serializables import \
    DoctorSchedule as serializable_DoctorSchedule
from proxy.custom_serializables import \
    NextAvailableSlot as serializable_NextAvailableSlot
from proxy.custom_serializables import \
    SlotAvailability as serializable_SlotAvailability
from proxy.custom_serializers import ObjectSerializer as custom_serializer
from proxy.custom_views import ProxyView
from utils import custom_viewsets
from utils.custom_permissions import IsPatientUser
from utils.exceptions import InvalidRequest
from utils.utils import manipal_admin_object


class DoctorsAPIView(custom_viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    search_fields = [
        'name', 'hospital_departments__department__name', 'hospital__code', 'code', 'id', 'hospital_departments__department__code', 'hospital_departments__department__id']
    filter_backends = (filters.SearchFilter,
                       filters.OrderingFilter, DjangoFilterBackend)
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    ordering = ('name',)
    filter_fields = ('hospital_departments__department__id',)
    create_success_message = None
    list_success_message = 'Doctors list returned successfully!'
    retrieve_success_message = 'Doctors information returned successfully!'
    update_success_message = None

    def get_queryset(self):
        if manipal_admin_object(self.request):
            return super().get_queryset().distinct()

        location_id = self.request.query_params.get('location_id', None)
        date = self.request.query_params.get('date', None)

        return Doctor.objects.filter(hospital_departments__hospital__id=location_id).filter(
            (Q(end_date__gte=date) | Q(end_date__isnull=True)) &
            Q(start_date__lte=datetime.now().date())).distinct()


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
        hv_price, vc_price, pr_price = 0, 0, 0
        hv_price, *vc_pr_price = price.split("-")
        if vc_pr_price:
            vc_price, *pr_price = vc_pr_price
            if pr_price:
                pr_price, *rem = pr_price
        morning_slot, afternoon_slot, evening_slot, slot_list = [], [], [], []
        if slots:
            slot_list = ast.literal_eval(slots)
        response = {}
        for slot in slot_list:
            time_format = ""
            appointment_type = "HV"
            if "HVVC" in slot['startTime']:
                time_format = '%d %b, %Y %I:%M:%S %p(HVVC)'
                appointment_type = "HVVC"
            elif "VC" in slot['startTime']:
                time_format = '%d %b, %Y %I:%M:%S %p(VC)'
                appointment_type = "VC"
            elif "PR" in slot['startTime']:
                time_format = '%d %b, %Y %I:%M:%S %p(PR)'
                appointment_type = "PR"
            else:
                time_format = '%d %b, %Y %I:%M:%S %p(HV)'
            time = datetime.strptime(
                slot['startTime'], time_format).time()
            if time.hour < 12:
                morning_slot.append({"slot": time.strftime(
                    "%I:%M:%S %p"), "type": appointment_type})
            elif (time.hour >= 12) and (time.hour < 17):
                afternoon_slot.append({"slot": time.strftime(
                    "%I:%M:%S %p"), "type": appointment_type})
            else:
                evening_slot.append({"slot": time.strftime(
                    "%I:%M:%S %p"), "type": appointment_type})
        response["morning_slot"] = morning_slot
        response["afternoon_slot"] = afternoon_slot
        response["evening_slot"] = evening_slot
        response["hv_price"] = hv_price
        response["vc_price"] = vc_price
        response["prime_price"] = pr_price
        return self.custom_success_response(message='Available slots',
                                            success=True, data=response)


class DoctorScheduleView(ProxyView):
    source = 'weeklySchedule'
    permission_classes = [IsPatientUser]

    def get_request_data(self, request):
        schedule = serializable_DoctorSchedule(**request.data)
        request_data = custom_serializer().serialize(schedule, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response.content)
        schedule_lists = root.find("ScheduleList").text
        schedule_list = []
        records = {}
        if schedule_lists:
            schedule_list = ast.literal_eval(schedule_lists)
        for record in schedule_list:
            hospital = record["Hosp"]
            hospital_description = Hospital.objects.filter(
                code=hospital).first().description
            if hospital_description in records:
                records[hospital_description].append(record)
            else:
                records[hospital_description] = []
                records[hospital_description].append(record)

        return self.custom_success_response(message='Available slots',
                                            success=True, data=records)


class NextSlotAvailable(ProxyView):
    source = 'NextAvailableSlotDate'
    permission_classes = [AllowAny]

    def get_request_data(self, request):
        data = request.data
        date = data.pop("date")
        y, m, d = date.split("-")
        data["schedule_date"] = d + m + y
        slots = serializable_NextAvailableSlot(**request.data)
        request_data = custom_serializer().serialize(slots, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response.content)
        response_message = "We are unable to cancel the appointment. Please Try again"
        success_status = False
        response_data = {}
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            next_date = root.find("nextdate").text
            status = root.find("Status").text
            message = root.find("Message").text
            response_success = True
            response_message = message
            response_data["next_slot"] = next_date
        return self.custom_success_response(message=response_message,
                                            success=response_success, data=response_data)


@api_view(['POST'])
@permission_classes([AllowAny])
def sign_up(request):
    code = request.data.get('user_name')
    password = request.data.get('password')  
    if not (code and password):
        raise ValidationError("Username or Password is Missing")

    doctor = Doctor.objects.filter(code=code).first()
    if not doctor:
        raise ValidationError("Doctor does not Exist")
    doctor.set_password(password)
    doctor.is_active = True
    doctor.save()
    data = {
        "message":  "Sign up successful!"
    }
    return Response(data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    code = request.data.get('user_name')
    password = request.data.get('password')  
    if not (code and password):
        raise ValidationError("Username or Password is Missing")

    doctor = Doctor.objects.filter(code=code).first()
    if not doctor:
        raise ValidationError("Doctor does not Exist")
    hash_password = doctor.password
    match_password = check_password(password, hash_password)
    if not match_password:
        raise ValidationError("Password is not correct")
    payload = jwt_payload_handler(doctor)
    payload["username"] = doctor.code
    token = jwt_encode_handler(payload)
    expiration = datetime.utcnow(
    ) + settings.JWT_AUTH['JWT_EXPIRATION_DELTA']
    expiration_epoch = expiration.timestamp()
    serializer = DoctorSerializer(doctor)
    data = {
        "data" : serializer.data,
        "message":  "Login successful!",
        "token": token,
        "token_expiration": expiration_epoch
    }
    return Response(data, status=status.HTTP_200_OK)
