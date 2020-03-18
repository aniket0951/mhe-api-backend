from rest_framework import serializers

from apps.health_packages.serializers import HealthPackageSerializer
from apps.lab_and_radiology_items.serializers import LabRadiologyItemSerializer
from apps.master_data.serializers import HospitalSerializer
from apps.patients.serializers import CurrentPatientUserDefault
from utils.serializers import DynamicFieldsModelSerializer

from .models import HealthPackageCart, HomeCollectionCart


class HealthPackageCartSerializer(DynamicFieldsModelSerializer):
    patient_info = serializers.UUIDField(write_only=True,
                                         default=CurrentPatientUserDefault())

    class Meta:
        model = HealthPackageCart
        fields = '__all__'

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        if instance.health_packages:
            response_object["health_packages"] = HealthPackageSerializer(instance.health_packages, many=True,
                                                                         context={
                                                                             "hospital__id": instance.hospital.id
                                                                         }).data
        if instance.hospital:
            response_object['hospital'] = HospitalSerializer(
                instance.hospital).data

        return response_object


class HomeCollectionCartSerializer(DynamicFieldsModelSerializer):
    patient_info = serializers.UUIDField(write_only=True,
                                         default=CurrentPatientUserDefault())

    class Meta:
        model = HomeCollectionCart
        fields = '__all__'

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        if instance.home_collections:
            response_object["home_collections"] = LabRadiologyItemSerializer(instance.home_collections, many=True,
                                                                             context={
                                                                                 "hospital__id": instance.hospital.id
                                                                             }).data
        if instance.hospital:
            response_object['hospital'] = HospitalSerializer(
                instance.hospital).data

        return response_object
