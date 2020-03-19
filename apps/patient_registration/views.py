from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import ast
import json
import xml.etree.ElementTree as ET
import requests
from django.core import serializers
from proxy.custom_serializables import \
    CreateUHID as serializable_CreateUHID
from proxy.custom_serializers import ObjectSerializer as custom_serializer
from proxy.custom_views import ProxyView

from utils.custom_permissions import IsPatientUser

from .models import (Country, Gender, IDProof, MaritalStatus, Nationality,
                     Province, Region, Relation, Religion, Speciality, Title)
from .exceptions import FieldMissingValidationException
from .serializers import (CountrySerializer, GenderSerializer,
                          IDProofSerializer, MaritalStatusSerializer,
                          NationalitySerializer, ProvinceSerializer,
                          RegionSerializer, RelationSerializer,
                          ReligionSerializer, SpecialitySerializer,
                          TitleSerializer)

from apps.patients.models import FamilyMember, Patient
from apps.patients.serializers import PatientSerializer, FamilyMemberSerializer


class RegistrationAPIView(ListAPIView):
    permission_classes = [IsPatientUser]

    def list(self, request, *args, **kwargs):
        registration_details = {}
        registration_details['country'] = CountrySerializer(
            Country.objects.all(), many=True).data
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
        registration_details['province'] = ProvinceSerializer(
            Province.objects.all(), many=True).data
        registration_details['region'] = RegionSerializer(
            Region.objects.all(), many=True).data
        registration_details['relation'] = RelationSerializer(
            Relation.objects.all(), many=True).data
        registration_details['religion'] = ReligionSerializer(
            Religion.objects.all(), many=True).data
        registration_details['title'] = TitleSerializer(
            Title.objects.all(), many=True).data
        return Response(registration_details, status=status.HTTP_200_OK)

class UHIDRegistrationView(ProxyView):
    source = 'SavePreRegistration'
    permission_classes = [IsPatientUser]

    def get_request_data(self, request):
        data = request.data
        user_id = data.pop("user_id",None)
        uhid_registration = serializable_CreateUHID(**request.data)
        request_data = custom_serializer().serialize(uhid_registration, 'XML')
        data["user_id"] =user_id
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        response_message = "Please try again"
        response_status = False
        response_data = {}
        if response.status_code == 200:
            user_id = self.request.data["user_id"]
            root = ET.fromstring(response.content)
            status = root.find("Status").text
            message = root.find("Message").text
            if status == "Failed":
                raise FieldMissingValidationException
            pre_registration_number = root.find("PreRegistrationNumber").text
            import pdb; pdb.set_trace()
            print(pre_registration_number)
            response_status = True
            response_message = message
            response_data["pre_registration_number"] = pre_registration_number
            
            if user_id:
                family_member = FamilyMember.objects.filter(id = user_id).first()
                family_serializer = FamilyMemberSerializer(family_member, data = response_data, partial = True)
                family_serializer.is_valid(raise_exception=True)
                family_serializer.save()
            else:
                patient = Patient.objects.filter(id = self.request.user.id).first()
                patient_serializer = PatientSerializer(patient, data = response_data, partial = True)
                patient_serializer.is_valid(raise_exception=True)
                patient_serializer.save()
        return self.custom_success_response(message=response_message,
                                            success=response_status, data=response_data)
