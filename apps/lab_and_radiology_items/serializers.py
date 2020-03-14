from rest_framework import serializers

from apps.master_data.models import HomeCareService
from apps.patients.serializers import (CurrentPatientUserDefault,
FamilyMemberSerializer,
                                       PatientAddressSerializer)
from utils.serializers import DynamicFieldsModelSerializer

from .models import (LabRadiologyItem, LabRadiologyItemPricing,
                     PatientServiceAppointment)


class LabRadiologyItemPricingSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = LabRadiologyItemPricing
        exclude = ('created_at', 'updated_at', 'id')


class LabRadiologyItemSerializer(DynamicFieldsModelSerializer):
    price = serializers.SerializerMethodField()

    class Meta:
        model = LabRadiologyItem
        exclude = ('created_at', 'updated_at',
                   'billing_sub_group', 'billing_group')

    def get_price(self, instance):
        hospital_id = self.context['request'].query_params.get('hospital__id')
        return instance.lab_radiology_item_pricing.get(hospital_id=hospital_id).price

class HomeCareServiceSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = HomeCareService
        exclude = ('created_at', 'updated_at',)


class PatientServiceAppointmentSerializer(DynamicFieldsModelSerializer):
    patient = serializers.UUIDField(write_only=True,
                                         default=CurrentPatientUserDefault())

    class Meta:
        model = PatientServiceAppointment
        fields = '__all__'


    def to_representation(self, instance):
        response_object = super().to_representation(instance)

        if instance.service:
            response_object['service'] = HomeCareServiceSerializer(instance.service).data

        if instance.address:
            response_object['address'] = PatientAddressSerializer(instance.address).data
            
        if instance.family_member:
            response_object['family_member'] = FamilyMemberSerializer(instance.family_member).data
        
        
        return response_object
