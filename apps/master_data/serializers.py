import logging
from django.contrib.gis.db.models.functions import Distance as Django_Distance
from django.contrib.gis.geos import Point, fromstr

from rest_framework import serializers
from utils.serializers import DynamicFieldsModelSerializer

from .models import (AmbulanceContact, Company, Department, EmergencyContact,
                     Hospital, HospitalDepartment, Specialisation, Components, CompanyDomain, Configurations)
from rest_framework.serializers import ValidationError
from utils.custom_validation import ValidationUtil

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
        response_object['hospital_contact'] = None
        if ambulance_contact_object:
            response_object['hospital_contact'] = {
                "id":str(ambulance_contact_object.id),
                "contact":str(ambulance_contact_object.mobile)
            }

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
    hospital = HospitalSerializer()

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
            response_object["component_ids"] = ComponentsSerializer(instance.component_ids, many = True).data
        
        return response_object
    
    def update(self, instance, validated_data):
        restriced_fields = [
                    'name'
                ]
        validated_data = {
            k: v for k, v in validated_data.items() if not k in restriced_fields}
        validate_fields = ["domain"]
        validated_fields = [ k for k, v in validated_data.items() if k in validate_fields and v and not ValidationUtil.check_Domain_Corporate(v)]
        if validated_fields:
            raise ValidationError("Only vaild domain format @domain.com is allowed %s"%(str(validated_fields[0])))
        
        return super().update(instance, validated_data)


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

class ConfigurationSerializer(DynamicFieldsModelSerializer):

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        if instance.allowed_components:
            response_object["allowed_components"] = ComponentsSerializer(instance.allowed_components, many = True).data
        return response_object
    class Meta:
        model = Configurations
        exclude = ('created_at', 'updated_at',)
        