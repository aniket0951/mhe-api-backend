import logging
from django.contrib.gis.db.models.functions import Distance as Django_Distance
from django.contrib.gis.geos import Point, fromstr

from rest_framework import serializers
from utils.serializers import DynamicFieldsModelSerializer

from .models import (AmbulanceContact, Company, Department, EmergencyContact,
                     Hospital, HospitalDepartment, Specialisation, Components, CompanyDomain)

_logger = logging.getLogger("django")

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
        except Exception as e:
            _logger.error("Error in to_representation HospitalSerializer: %s"%(str(e)))

        ambulance_contact_object = AmbulanceContact.objects.filter(hospital_id=instance.id).first()
        response_object['hospital_contact'] = {}
        if ambulance_contact_object and ambulance_contact_object.mobile:
            response_object['hospital_contact'].update({
                "id":ambulance_contact_object.id,
                "contact":str(ambulance_contact_object.mobile)
            })

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

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        if instance.department and instance.department.name:
            response_object["department"]["name"] = instance.department.name
        return response_object


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


class HospitalSpecificSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Hospital
        exclude = ('created_at', 'updated_at',)


class CompanySerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Company
        exclude = ('created_at', 'updated_at',)

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        if instance.hospital_info:
            response_object['hospital_info'] = HospitalSerializer(
                instance.hospital_info, many=True).data
        if instance.component_ids:
            response_object["component_ids"] = ComponentsSerializer(instance.components, many = True).data
        
        return response_object


class EmergencyContactSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = EmergencyContact
        exclude = ('created_at', 'updated_at',)


class ComponentsSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = Components
        exclude = ('created_at', 'updated_at',)

class CompanyDomainsSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = CompanyDomain
        exclude = ('created_at', 'updated_at',)