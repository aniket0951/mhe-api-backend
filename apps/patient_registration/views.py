import ast
import json
import xml.etree.ElementTree as ET

import requests
from django.core import serializers

from apps.patients.models import FamilyMember, Patient
from apps.patients.serializers import FamilyMemberSpecificSerializer, PatientSerializer
from proxy.custom_serializables import CreateUHID as serializable_CreateUHID
from proxy.custom_serializers import ObjectSerializer as custom_serializer
from proxy.custom_views import ProxyView
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from utils.custom_permissions import IsPatientUser

from .exceptions import FieldMissingValidationException
from .models import (Country, Gender, IDProof, MaritalStatus, Nationality,
                     Province, Region, Relation, Religion, Speciality, Title)
from .serializers import (CountrySerializer, GenderSerializer,
                          IDProofSerializer, MaritalStatusSerializer,
                          NationalitySerializer, ProvinceSerializer,
                          RegionSerializer, RelationSerializer,
                          ReligionSerializer, SpecialitySerializer,
                          TitleSerializer)


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
        request.data["dob"] = "".join(request.data["dob"].split("/"))
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

            if user_id:
                family_member = FamilyMember.objects.filter(id=user_id).first()
                family_serializer = FamilyMemberSpecificSerializer(
                    family_member, data=response_data, partial=True)
                family_serializer.is_valid(raise_exception=True)
                family_serializer.save()
            else:
                patient = Patient.objects.filter(
                    id=self.request.user.id).first()
                patient_serializer = PatientSerializer(
                    patient, data=response_data, partial=True)
                patient_serializer.is_valid(raise_exception=True)
                patient_serializer.save()
        return self.custom_success_response(message=response_message,
                                            success=response_status, data=response_data)
