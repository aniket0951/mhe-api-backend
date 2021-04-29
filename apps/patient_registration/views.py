import ast
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import logging
import requests
from django.core import serializers
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.patients.models import FamilyMember, Patient
from apps.patients.serializers import (FamilyMemberSpecificSerializer,
                                       PatientSerializer,
                                       PatientSpecificSerializer)
from proxy.custom_serializables import CreateUHID as serializable_CreateUHID
from proxy.custom_serializers import ObjectSerializer as custom_serializer
from proxy.custom_views import ProxyView
from utils import custom_viewsets
from utils.custom_permissions import IsManipalAdminUser, IsPatientUser

from .exceptions import FieldMissingValidationException
from .models import (City, Country, Gender, IDProof, Language, MaritalStatus,
                     Nationality, Province, Region, Relation, Religion,
                     Speciality, Title, Zipcode)
from .serializers import (CitySerializer, CountrySerializer, GenderSerializer,
                          IDProofSerializer, LanguageSerializer,
                          MaritalStatusSerializer, NationalitySerializer,
                          ProvinceSerializer, RegionSerializer,
                          RelationSerializer, ReligionSerializer,
                          SpecialitySerializer, TitleSerializer,
                          ZipcodeSerializer)
logger = logging.getLogger("django")

class RegistrationAPIView(ListAPIView):
    permission_classes = [IsPatientUser | IsManipalAdminUser]

    def list(self, request, *args, **kwargs):
        registration_details = {}
        registration_details['speciality'] = SpecialitySerializer(
            Speciality.objects.all(), many=True).data
        registration_details['gender'] = GenderSerializer(
            Gender.objects.all(), many=True).data
        registration_details['id_proof'] = IDProofSerializer(
            IDProof.objects.all(), many=True).data
        registration_details['marital_status'] = MaritalStatusSerializer(
            MaritalStatus.objects.all(), many=True).data
        registration_details['nationality'] = NationalitySerializer(
            Nationality.objects.all(), many=True).data
        registration_details['relation'] = RelationSerializer(
            Relation.objects.all(), many=True).data
        registration_details['religion'] = ReligionSerializer(
            Religion.objects.all(), many=True).data
        registration_details['title'] = TitleSerializer(
            Title.objects.all(), many=True).data
        return Response(registration_details, status=status.HTTP_200_OK)

class LanguageViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsPatientUser]
    model = Language
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    list_success_message = 'Languages list returned successfully!'

    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    search_fields = ['description', ]
    ordering_fields = ('description',)

    def get_queryset(self):
        return super().get_queryset().filter(from_date__lte=datetime.today().date()).filter(
            Q(to_date__isnull=True) | Q(to_date__gte=datetime.today().date()))



class CountryViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsPatientUser]
    model = Country
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    list_success_message = 'Countries list returned successfully!'

    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    search_fields = ['description', ]
    ordering_fields = ('description',)

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True,
                                             from_date__lte=datetime.today().date()).filter(
            Q(to_date__isnull=True) | Q(to_date__gte=datetime.today().date()))


class RegionViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsPatientUser]
    model = Region
    queryset = Region.objects.all().prefetch_related('country')
    serializer_class = RegionSerializer
    list_success_message = 'Regions list returned successfully!'

    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    search_fields = ['description', ]
    ordering_fields = ('description',)
    filter_fields = ('country',)

class ProvinceViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsPatientUser]
    model = Province
    queryset = Province.objects.all().prefetch_related('region',
                                                   'region__country')
    serializer_class = ProvinceSerializer
    list_success_message = 'Provinces list returned successfully!'

    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    search_fields = ['description', ]
    ordering_fields = ('description',)
    filter_fields = ('region',)

class CityViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsPatientUser]
    model = City
    queryset = City.objects.all().prefetch_related('province', 'province__region',
                                                   'province__region__country')
    serializer_class = CitySerializer
    list_success_message = 'Cities list returned successfully!'

    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    search_fields = ['description', ]
    ordering_fields = ('description',)
    filter_fields = ('province',)


class ZipcodeViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsPatientUser]
    model = Zipcode
    queryset = Zipcode.objects.all().prefetch_related('city',
                                                      'city__province__region',
                                                      'city__province__region__country')
    serializer_class = ZipcodeSerializer
    list_success_message = 'Zipcodes list returned successfully!'

    filter_backends = (DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter,)
    search_fields = ['code', ]
    ordering_fields = ('code',)
    filter_fields = ('city',)


class UHIDRegistrationView(ProxyView):
    source = 'SavePreRegistration'
    permission_classes = [IsPatientUser]

    def get_request_data(self, request):
        d, m, y = request.data["dob"].split("/")
        request.data["dob"] = m + d + y
        uhid_registration = serializable_CreateUHID(request.data)
        request_data = custom_serializer().serialize(uhid_registration, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        response_message = "Please try again"
        response_status = False
        response_data = {}
        if response.status_code == 200:
            user_id = self.request.data.get("user_id", None)
            root = ET.fromstring(response.content)
            status = root.find("Status").text
            message = root.find("Message").text
            if status == "Failed":
                raise FieldMissingValidationException
            pre_registration_number = root.find("PreRegistrationNumber").text
            response_status = True
            response_message = message
            response_data["pre_registration_number"] = pre_registration_number
            logger.info("request_dob :" + self.request.data["dob"])
            dob_obj = datetime.strptime(self.request.data["dob"], "%m%d%Y")
            logger.info("dob_obj : %s"%(str(dob_obj)))
            response_data["dob"] = dob_obj.date()

            if user_id:
                family_member = FamilyMember.objects.filter(id=user_id).first()
                family_serializer = FamilyMemberSpecificSerializer(
                    family_member, data=response_data, partial=True)
                family_serializer.is_valid(raise_exception=True)
                family_serializer.save()
            else:
                patient = Patient.objects.filter(
                    id=self.request.user.id).first()
                patient_serializer = PatientSpecificSerializer(
                    patient, data=response_data, partial=True)
                patient_serializer.is_valid(raise_exception=True)
                patient_serializer.save()
        return self.custom_success_response(message=response_message,
                                            success=response_status, data=response_data)
