from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from utils.custom_permissions import IsPatientUser

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
        return Response(registration_details)
