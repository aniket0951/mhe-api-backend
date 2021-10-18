import ast
import logging
import xml.etree.ElementTree as ET

from django.conf import settings
from django.db.models import Q
from django.utils.timezone import datetime
from datetime import date, timedelta

from apps.doctors.exceptions import DoctorDoesNotExistsValidationException
from apps.doctors.models import Doctor, DoctorsWeeklySchedule
from apps.doctors.utils import process_slots
from apps.doctors.serializers import (DoctorSerializer, DoctorsWeeklyScheduleSerializer,)
from apps.master_data.models import Department, Hospital
from django_filters.rest_framework import DjangoFilterBackend
from proxy.custom_serializables import \
    DoctorConsultationCharges as serializable_DoctorConsultationCharges
from proxy.custom_serializables import \
    DoctorSchedule as serializable_DoctorSchedule
from proxy.custom_serializables import DoctotLogin as serializable_DoctotLogin
from proxy.custom_serializables import \
    NextAvailableSlot as serializable_NextAvailableSlot
from proxy.custom_serializables import \
    RescheduleSlot as serializable_RescheduleSlot
from proxy.custom_serializables import \
    SlotAvailability as serializable_SlotAvailability
from proxy.custom_serializers import ObjectSerializer as custom_serializer
from proxy.custom_views import ProxyView
from rest_framework import filters
from rest_framework.permissions import AllowAny
from rest_framework.serializers import ValidationError
from rest_framework_jwt.utils import jwt_encode_handler, jwt_payload_handler

from utils import custom_viewsets
from utils.custom_permissions import BlacklistDestroyMethodPermission, BlacklistUpdateMethodPermission, InternalAPICall, IsManipalAdminUser, IsPatientUser
from utils.exceptions import InvalidRequest
from utils.utils import manipal_admin_object,patient_user_object
from .constants import DoctorsConstants
from utils.custom_jwt_whitelisted_tokens import WhiteListedJWTTokenUtil

logger = logging.getLogger("django")

class DoctorsAPIView(custom_viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    search_fields = ['name', 'hospital_departments__department__name', 'hospital__code', 'code', 'id', 'hospital_departments__department__code', 'hospital_departments__department__id']
    filter_backends = (filters.SearchFilter,filters.OrderingFilter, DjangoFilterBackend)
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    ordering = ('name',)
    filter_fields = ('hospital_departments__department__id',)
    create_success_message = None
    list_success_message = 'Doctors list returned successfully!'
    retrieve_success_message = 'Doctors information returned successfully!'
    update_success_message = None

    def get_queryset(self):
        admin_object = manipal_admin_object(self.request)
        if admin_object:
            if admin_object.hospital:
                location_id = admin_object.hospital.id
                return Doctor.objects.filter(hospital_departments__hospital__id=location_id).distinct()
            return super().get_queryset().distinct()

        location_id = self.request.query_params.get('location_id')
        if not location_id:
            raise ValidationError("location_id is mandatory.")
        date = self.request.query_params.get('date')
        if not date:
            raise ValidationError("date is mandatory.")

        qs = Doctor.objects.filter(
                    hospital_departments__hospital__id=location_id
                ).filter(
                    (
                        Q(end_date__gte=date) | Q(end_date__isnull=True)) &
                        Q(start_date__lte=date) & Q(is_online_appointment_enable=True)
                    ).distinct()

        if patient_user_object(self.request):

            hospital_departments__department__id = self.request.query_params.get("hospital_departments__department__id", None)
            if not hospital_departments__department__id:
                qs = qs.exclude(Q(hospital_departments__service__in=[settings.COVID_SERVICE]))

        return qs

def extract_slots(slot_list,slot_blocking_duration=0):
    morning_slot, afternoon_slot, evening_slot = [], [], []
    services = {"HV":False,"VC":False,"PR":False}
    current_time = datetime.now() + timedelta(minutes=slot_blocking_duration)
    
    for slot in slot_list:
        time_format = ""
        appointment_type = "HV"
        end_time_format = '%d %b, %Y %I:%M:%S %p'

        if "HVVC" in slot['startTime']:
            time_format = '%d %b, %Y %I:%M:%S %p(HVVC)'
            appointment_type = "HVVC"
            services["HV"] = True
            services["VC"] = True

        elif "VC" in slot['startTime']:
            time_format = '%d %b, %Y %I:%M:%S %p(VC)'
            appointment_type = "VC"
            services["VC"] = True

        elif "PR" in slot['startTime']:
            time_format = '%d %b, %Y %I:%M:%S %p(PR)'
            appointment_type = "PR"
            services["PR"] = True

        else:
            time_format = '%d %b, %Y %I:%M:%S %p(HV)'
            services["HV"] = True

        time = datetime.strptime(slot['startTime'], time_format).time()
        end_time = datetime.strptime(slot['endTime'], end_time_format).time()

        if time < current_time:
            continue
        
        slot_duration_td = datetime.combine(date.today(), end_time) - datetime.combine(date.today(), time)
        slot_duration_minute = (slot_duration_td.seconds//60)%60
        
        if time.hour < 12:
            morning_slot.append({"slot": time.strftime(DoctorsConstants.APPOINTMENT_SLOT_TIME_FORMAT), "type": appointment_type, 'slot_duration':slot_duration_minute})
        elif (time.hour >= 12) and (time.hour < 17):
            afternoon_slot.append({"slot": time.strftime(DoctorsConstants.APPOINTMENT_SLOT_TIME_FORMAT), "type": appointment_type, 'slot_duration':slot_duration_minute})
        else:
            evening_slot.append({"slot": time.strftime(DoctorsConstants.APPOINTMENT_SLOT_TIME_FORMAT), "type": appointment_type, 'slot_duration':slot_duration_minute})

    return morning_slot, afternoon_slot, evening_slot, services

def get_doctor_instace(data,date):
    doctor = None
    try:
        doctor = Doctor.objects.filter(
                            id=data.pop("doctor_id"), 
                            hospital_departments__hospital__id=data.get("hospital_id"), 
                            hospital_departments__department__id=data.get("department_id")
                        ).filter(
                            Q(end_date__gte=date) | Q(end_date__isnull=True)
                        )
    except Exception as e:
        logger.info("Exception in DoctorSlotAvailability: %s"%(str(e)))
        raise InvalidRequest
    if not doctor:
        raise ValidationError("Doctor is not available on the selected date.")
    return doctor

class DoctorSlotAvailability(ProxyView):
    source = 'getDoctorPriceAndSchedule'
    permission_classes = [IsPatientUser]

    def get_request_data(self, request):
        data = request.data
        date = data.pop("date")

        doctor = get_doctor_instace(data,date)

        hospital = Hospital.objects.filter(id=data.pop("hospital_id")).first()
        department = Department.objects.filter(id=data.pop("department_id")).first()

        y, m, d = date.split("-")
        data["schedule_date"] = d + m + y
        data["doctor_code"] = doctor[0].code
        data["location_code"] = hospital.code
        data["speciality_code"] = department.code

        slots = serializable_SlotAvailability(**request.data)
        request_data = custom_serializer().serialize(slots, 'XML')

        request.data["hospital_id"] = hospital

        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response.content)
        slots = root.find("timeSlots").text
        price = root.find("price").text
        status = root.find("Status").text
        hospital = self.request.data.get("hospital_id")
        slot_blocking_duration = 0

        if hospital and hospital.slot_blocking_duration:
            slot_blocking_duration = hospital.slot_blocking_duration

        hv_price, vc_price, pr_price = 0, 0, 0
        morning_slot, afternoon_slot, evening_slot = [], [], []
        
        response = {}
        services = {"HV":False,"VC":False,"PR":False}
        if status == "SUCCESS":

            hv_price, *vc_pr_price = price.split("-")
            
            if vc_pr_price:
                
                vc_price, *pr_price = vc_pr_price
                if pr_price:
                    pr_price, *rem = pr_price

            if slots:

                slot_list = ast.literal_eval(slots)
                morning_slot, afternoon_slot, evening_slot, services = extract_slots(slot_list,slot_blocking_duration)
            
        response["morning_slot"] = morning_slot
        response["afternoon_slot"] = afternoon_slot
        response["evening_slot"] = evening_slot
        response["services"] = services
        response["hv_price"] = hv_price
        response["vc_price"] = vc_price
        response["prime_price"] = pr_price

        return self.custom_success_response(
                            message=DoctorsConstants.AVAILABLE_SLOTS, 
                            success=True, 
                            data=response
                        )


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
        response_message = "We are unable to cancel the appointment. Please Try again"
        response_success = False
        response_data = {}
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            next_date = root.find("nextdate").text
            message = root.find("Message").text
            response_success = True
            response_message = message
            response_data["next_slot"] = next_date
        return self.custom_success_response(message=response_message,
                                            success=response_success, data=response_data)


class DoctorloginView(ProxyView):
    source = 'uservalidation'
    permission_classes = [AllowAny]

    def get_request_data(self, request):
        appointment_identifier = request.data.pop(
            "appointment_identifier", None)
        user_id = request.data.get("user_id")
        if user_id and user_id.upper().startswith("MMH"):
            request.data["location_code"] = "MMH"
        schedule = serializable_DoctotLogin(**request.data)
        request_data = custom_serializer().serialize(schedule, 'XML')
        request.data["appointment_identifier"] = appointment_identifier
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response.content)
        status = root.find("Status").text
        success = False
        if status == "1":
            login_response = root.find("loginresp").text
            login_response = ast.literal_eval(login_response)
            if login_response:
                
                login_response_json = login_response[0]
                login_status = login_response_json["Status"]
                if login_status == "Success":
                    doctor_code = login_response_json["CTPCP_Code"]
                    login_response_json["Hosp"]

                    doctor = Doctor.objects.filter(code=doctor_code).exclude(hospital_departments=None).first()
                    payload = jwt_payload_handler(doctor)
                    payload["username"] = doctor.code
                    token = jwt_encode_handler(payload)
                    expiration = datetime.utcnow() + settings.JWT_AUTH['JWT_EXPIRATION_DELTA']
                    expiration_epoch = expiration.timestamp()
                    serializer = DoctorSerializer(doctor)

                    WhiteListedJWTTokenUtil.create_token(doctor,token)

                    message = "login is successful"
                    success = True
                    data = {
                        "data": serializer.data,
                        "message":  "Login successful!",
                        "token": token,
                        "token_expiration": expiration_epoch
                    }
                    return self.custom_success_response(message=message,
                                                        success=success, data=data)
        raise ValidationError("Login Failed")


class DoctorRescheduleSlot(ProxyView):
    source = 'getSlotForAppntType'
    permission_classes = [IsPatientUser | IsManipalAdminUser]

    def get_request_data(self, request):
        slots = serializable_RescheduleSlot(**request.data)
        request_data = custom_serializer().serialize(slots, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response.content)
        slots = root.find("timeSlots").text
        price = root.find("price").text
        status = root.find("Status").text

        slot_blocking_duration = 0
        if self.request.data.get("location_code"):
            hospital = Hospital.objects.filter(code=self.request.data.get("location_code")).first()
            slot_blocking_duration = hospital.slot_blocking_duration if hospital else 0

        morning_slot, afternoon_slot, evening_slot = [], [], []
        services = {"HV":False,"VC":False,"PR":False}

        response = {}
        if status == "SUCCESS":
            morning_slot, afternoon_slot, evening_slot, services = process_slots(slots,slot_blocking_duration)
            response["price"] = price.split("-")[0]

        response["morning_slot"] = morning_slot
        response["afternoon_slot"] = afternoon_slot
        response["evening_slot"] = evening_slot
        response["services"] = services
        return self.custom_success_response(message=DoctorsConstants.AVAILABLE_SLOTS,success=True, data=response)


class DoctorScheduleView(ProxyView):
    source = 'weeklySchedule'
    permission_classes = [ IsPatientUser | InternalAPICall ]

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
            if schedule_list:
                hospital = schedule_list[0]["Hosp"]
                hospital_description = Hospital.objects.filter(code=hospital).first().description
                for record in schedule_list:
                    if hospital_description not in records:
                        records[hospital_description] = []
                    record["SessionType"] = record["SessionType"].replace("/","") 
                    records[hospital_description].append(record)
                
        return self.custom_success_response(message=DoctorsConstants.AVAILABLE_SLOTS,success=True, data=records)


class DoctorConsultationChargeView(ProxyView):
    source = 'getconsultationcharges'
    permission_classes = [AllowAny]

    def get_request_data(self, request):
        charges = serializable_DoctorConsultationCharges(**request.data)
        request_data = custom_serializer().serialize(charges, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response.content)
        status = root.find("Status").text
        data = dict()
        message = "Could not fetch the price for the doctor"
        success = False
        if status == "1":
            consultation_charges = root.find("consultchargesResp").text
            if consultation_charges:
                consultation_charges = ast.literal_eval(consultation_charges)
                data["hv_charge"] = consultation_charges[0]["OPDConsCharges"]
                data["vc_charge"] = consultation_charges[0]["VCConsCharges"]
                data["pr_charge"] = consultation_charges[0]["PRConsCharges"]
                data["plan_code"] = consultation_charges[0]["PlanCode"]
                message = "success"
                success = True
        return self.custom_success_response(
                                        message=message,
                                        success=success, 
                                        data=data
                                    )

class DoctorsWeeklyScheduleViewSet(custom_viewsets.CreateUpdateListRetrieveModelViewSet):
    
    queryset = DoctorsWeeklySchedule.objects.all()
    serializer_class = DoctorsWeeklyScheduleSerializer
    permission_classes = [IsPatientUser | IsManipalAdminUser]
    create_success_message = "Doctor's weekly schedule added successfully!"
    update_success_message = "Doctor's weekly schedule updated successfully!"
    list_success_message = "Doctor's weekly schedule returned successfully!"
    retrieve_success_message = "Doctor's weekly schedule returned successfully!"
    filter_backends = (
                DjangoFilterBackend,
                filters.SearchFilter, 
                filters.OrderingFilter
            )
    filter_fields = ['hospital','hospital__code','department','department__code','doctor','doctor__code']
    search_fields = ['hospital__code','hospital__description','department__code','department__name','doctor__code',"doctor__name"]
    ordering_fields = ('hospital','departnemt','doctor','-created_at',)
    
    def get_permissions(self):

        if self.action in ['list', 'retrieve']:
            permission_classes = [IsPatientUser | IsManipalAdminUser]
            return [permission() for permission in permission_classes]

        if self.action in ['create','partial_update']:
            permission_classes = [IsManipalAdminUser]
            return [permission() for permission in permission_classes]
        
        if self.action == 'update':
            permission_classes = [BlacklistUpdateMethodPermission]
            return [permission() for permission in permission_classes]

        if self.action == 'destroy':
            permission_classes = [BlacklistDestroyMethodPermission]
            return [permission() for permission in permission_classes]

        return super().get_permissions()