from rest_framework import serializers
from .models import HealthPackageCart
from utils.serializers import DynamicFieldsModelSerializer
from apps.patients.serializers import CurrentPatientUserDefault
from apps.health_packages.serializers import HealthPackageSerializer
from apps.master_data.serializers import HospitalSerializer

class HealthPackageCartSerializer(DynamicFieldsModelSerializer):
    patient_info = serializers.UUIDField(write_only=True,
                                    default=CurrentPatientUserDefault())

    class Meta:
        model = HealthPackageCart
        fields = '__all__'

    def to_representation(self, instance):
        response_object =  super().to_representation(instance)
        if instance.health_packages:
            response_object["health_packages"] = HealthPackageSerializer(instance.health_packages, many=True,
            context={
                    "hospital__id" : instance.hospital.id
            }).data
        if instance.hospital:
            response_object['hospital'] = HospitalSerializer(instance.hospital).data

        return response_object