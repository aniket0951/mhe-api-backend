from apps.health_packages.constants import HealthPackagesConstants
import ast
import json
import xml.etree.ElementTree as ET

from django.db.models import Exists, OuterRef, Q
from django.utils.timezone import datetime

from apps.cart_items.models import HealthPackageCart
from apps.master_data.models import Hospital, Specialisation
from django_filters.rest_framework import DjangoFilterBackend
from proxy.custom_serializables import \
    HealthPackagePrice as serializable_HealthPackagePrice
from proxy.custom_serializables import \
    SlotAvailability as serializable_SlotAvailability
from proxy.custom_serializers import ObjectSerializer as custom_serializer
from proxy.custom_views import ProxyView
from rest_framework import filters
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.serializers import ValidationError
from utils import custom_viewsets
from utils.custom_permissions import (BlacklistDestroyMethodPermission,
                                      BlacklistUpdateMethodPermission,
                                      IsManipalAdminUser, IsPatientUser)

from .exceptions import FeatureNotAvailableException
from .filters import HealthPackageFilter
from .models import HealthPackage, HealthPackagePricing
from .serializers import (HealthPackageDetailSerializer,
                          HealthPackageSerializer,
                          HealthPackageSpecialisationDetailSerializer,
                          HealthPackageSpecialisationSerializer)


class HealthPackageSpecialisationViewSet(custom_viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    model = Specialisation
    queryset = Specialisation.objects.all()
    serializer_class = HealthPackageSpecialisationSerializer
    detail_serializer_class = HealthPackageSpecialisationDetailSerializer
    create_success_message = "New health package specialisation is added successfully."
    list_success_message = 'Health package specialisation list returned successfully!'
    retrieve_success_message = 'Health package specialisation information returned successfully!'
    update_success_message = 'Health package specialisation information is updated successfuly!'
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    ordering_fields = ('description',)
    search_fields = ('description', 'code')

    def get_permissions(self):
        if self.action in ['list', 'retrieve', ]:
            permission_classes = [AllowAny]
            return [permission() for permission in permission_classes]

        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'retrieve' and hasattr(self, 'detail_serializer_class'):
            return self.detail_serializer_class
        return super().get_serializer_class()

    def get_queryset(self):
        hospital_id = self.request.query_params.get('hospital__id')

        if not hospital_id:
            raise ValidationError("Hospital ID is missing!")

        hospital_related_health_packages = HealthPackagePricing.objects.filter(
            hospital=hospital_id).values_list('health_package_id', flat=True)

        return Specialisation.objects.filter(health_package__id__in=hospital_related_health_packages).filter(
            (Q(end_date__gte=datetime.now().date()) | Q(end_date__isnull=True)) &
            Q(start_date__lte=datetime.now().date())).distinct('description',)


class HealthPackageViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    model = HealthPackage
    queryset = HealthPackage.objects.all()
    serializer_class = HealthPackageSerializer
    detail_serializer_class = HealthPackageDetailSerializer
    create_success_message = "New health package is added successfully."
    list_success_message = 'Health package list returned successfully!'
    retrieve_success_message = 'Health package information returned successfully!'
    update_success_message = 'Health package information is updated successfuly!'
    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    filter_class = HealthPackageFilter
    search_fields = [
        'name', 'code', 'included_health_tests__description', 'included_health_tests__code']
    ordering_fields = ('health_package_pricing__price', 'name')

    def get_permissions(self):
        if self.action in ['list', 'retrieve', ]:
            permission_classes = [AllowAny]
            return [permission() for permission in permission_classes]

        if self.action in ['partial_update', 'create']:
            permission_classes = [IsManipalAdminUser]
            return [permission() for permission in permission_classes]

        if self.action == 'update':
            permission_classes = [BlacklistUpdateMethodPermission]
            return [permission() for permission in permission_classes]

        if self.action == 'destroy':
            permission_classes = [BlacklistDestroyMethodPermission]
            return [permission() for permission in permission_classes]

        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'retrieve' and hasattr(self, 'detail_serializer_class'):
            return self.detail_serializer_class
        return super().get_serializer_class()

    def get_queryset(self):
        hospital_id = self.request.query_params.get('hospital__id')

        if not hospital_id:
            raise ValidationError("Hospital ID is missiing!")

        hospital_related_health_packages = HealthPackagePricing.objects.filter(
                                                        hospital=hospital_id
                                                    ).filter(
                                                        (
                                                            Q(end_date__gte=datetime.now().date()) | 
                                                            Q(end_date__isnull=True)
                                                        ) &
                                                            Q(start_date__lte=datetime.now().date())
                                                    ).values_list('health_package_id', flat=True)

        user_cart_packages = HealthPackageCart.objects.filter(
                                        patient_info_id = self.request.user.id,  
                                        health_packages = OuterRef('pk'), 
                                        hospital_id     = hospital_id
                                    )

        return HealthPackage.objects.filter(
                            id__in=hospital_related_health_packages
                        ).distinct().annotate(
                                        is_added_to_cart=Exists(user_cart_packages)
                                    )


class HealthPackageSlotAvailability(ProxyView):
    source = 'getDoctorPriceAndSchedule'
    permission_classes = [IsPatientUser]

    def get_request_data(self, request):
        data = request.data
        date = data.pop("date")
        location_code = data.get("location_code", None)
        if not location_code:
            raise ValidationError("Hospital code is missiing!")
        hospital = Hospital.objects.filter(code=location_code).first()
        y, m, d = date.split("-")
        if not hospital.is_health_package_online_purchase_supported:
            raise FeatureNotAvailableException
        data["doctor_code"] = hospital.health_package_doctor_code
        data["speciality_code"] = hospital.health_package_department_code
        data["schedule_date"] = d + m + y
        slots = serializable_SlotAvailability(**request.data)
        request_data = custom_serializer().serialize(slots, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response.content)
        slots = root.find("timeSlots").text
        price = root.find("price").text
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
                morning_slot.append({"slot": time.strftime(HealthPackagesConstants.SLOT_TIME_FORMAT), "type": appointment_type})
            elif (time.hour >= 12) and (time.hour < 17):
                afternoon_slot.append({"slot": time.strftime(HealthPackagesConstants.SLOT_TIME_FORMAT), "type": appointment_type})
            else:
                evening_slot.append({"slot": time.strftime(HealthPackagesConstants.SLOT_TIME_FORMAT), "type": appointment_type})
        response["morning_slot"] = morning_slot
        response["afternoon_slot"] = afternoon_slot
        response["evening_slot"] = evening_slot
        response["price"] = price
        return self.custom_success_response(message='Available slots',
                                            success=True, data=response)


class HealthPackagePrice(ProxyView):
    source = 'getpackageprice'
    permission_classes = [AllowAny]

    def get_request_data(self, request):
        price_obj = serializable_HealthPackagePrice(**request.data)
        request_data = custom_serializer().serialize(price_obj, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        root = ET.fromstring(response.content)
        message = "Please Try again"
        success_status = False
        response_message = {}
        if response.status_code == 200:
            root.find("Status").text
            message = root.find("Message").text
            if message == "Success":
                package_detail = root.find("packagepricedetails").text
                if package_detail:
                    success_status = True
                    total_package_info = ast.literal_eval(package_detail)
                    discounted_price = total_package_info['TotalPackagePrice']
                    response_message = total_package_info
                    response_message["discounted_price"] = discounted_price
                    message = discounted_price

        return self.custom_success_response(message=message,
                                            success=success_status, data=response_message)
