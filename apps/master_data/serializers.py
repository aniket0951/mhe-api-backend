from django.contrib.gis.db.models.functions import Distance as Django_Distance
from django.contrib.gis.geos import Point, fromstr

from rest_framework import serializers
from utils.serializers import DynamicFieldsModelSerializer

from .models import (AmbulanceContact, Department, Hospital,
                     HospitalDepartment, Specialisation)


class HospitalSerializer(DynamicFieldsModelSerializer):
    distance = serializers.CharField(
        source='calculated_distance', default=None)

    class Meta:
        model = Hospital
        exclude = ('created_at', 'updated_at',)

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        try:
            if 'distance' in response_object and instance.calculated_distance:
                response_object['distance'] = instance.calculated_distance.km
        except Exception:
            pass
        return response_object


class SpecialisationSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Specialisation
        exclude = ('created_at', 'updated_at',)


class DepartmentSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Department
        exclude = ('created_at', 'updated_at',)


class HospitalDepartmentSerializer(DynamicFieldsModelSerializer):
    department = DepartmentSerializer()

    class Meta:
        model = HospitalDepartment
        exclude = ('created_at', 'updated_at',)


class AmbulanceContactSerializer(DynamicFieldsModelSerializer):
    distance = serializers.CharField(
        source='calculated_distance', default=None)
    class Meta:
        model = AmbulanceContact
        exclude = ('created_at', 'updated_at',)
    
    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        if instance.hospital:
            response_object['hospital'] = HospitalSerializer(
                instance.hospital).data
        try:
            if 'distance' in response_object and instance.calculated_distance:
                response_object['distance'] = instance.calculated_distance.km
        except Exception:
            pass
        return response_object
