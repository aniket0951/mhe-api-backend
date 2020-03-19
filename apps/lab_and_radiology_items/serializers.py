from rest_framework import serializers

from apps.master_data.models import HomeCareService
from apps.master_data.serializers import HospitalSerializer
from apps.patients.serializers import (CurrentPatientUserDefault,
                                       FamilyMemberSerializer,
                                       PatientAddressSerializer,
                                       PatientSerializer)
from utils.serializers import DynamicFieldsModelSerializer
from utils.utils import generate_pre_signed_url

from .models import (HomeCollectionAppointment, LabRadiologyItem,
                     LabRadiologyItemPricing, PatientServiceAppointment,
                     UploadPrescription)


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
        if 'hospital__id' in self.context:
            hospital_id = self.context['hospital__id']
        else:
            hospital_id = self.context['request'].query_params.get(
                'hospital__id')
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
            response_object['service'] = HomeCareServiceSerializer(
                instance.service).data

        if instance.address:
            response_object['address'] = PatientAddressSerializer(
                instance.address).data

        if instance.family_member:
            response_object['family_member'] = FamilyMemberSerializer(
                instance.family_member,
                fields=('id', 'mobile', 'relation_name', 'uhid_number', 'display_picture', 'gender',
                        'first_name')).data

        response_object['patient'] = PatientSerializer(
            instance.patient,
            fields=('id', 'mobile', 'uhid_number', 'first_name', 'display_picture',
                    'email', 'gender')).data

        return response_object


class UploadPrescriptionSerializer(DynamicFieldsModelSerializer):
    patient = serializers.UUIDField(write_only=True,
                                    default=CurrentPatientUserDefault())

    class Meta:
        model = UploadPrescription
        fields = '__all__'

    def to_representation(self, instance):
        response_object = super().to_representation(instance)

        try:
            if instance.document:
                response_object['document'] = generate_pre_signed_url(
                    instance.document.url)
        except Exception as error:
            print(error)
            response_object['display_picture'] = None

        if instance.address:
            response_object['address'] = PatientAddressSerializer(
                instance.address).data

        if instance.family_member:
            response_object['family_member'] = FamilyMemberSerializer(
                instance.family_member,
                fields=('id', 'mobile', 'relation_name', 'uhid_number', 'display_picture', 'gender',
                        'first_name')).data

        response_object['patient'] = PatientSerializer(
            instance.patient,
            fields=('id', 'mobile', 'uhid_number', 'first_name', 'display_picture',
                    'email', 'gender')).data

        return response_object


class HomeCollectionAppointmentSerializer(DynamicFieldsModelSerializer):
    patient = serializers.UUIDField(write_only=True,
                                    default=CurrentPatientUserDefault())

    class Meta:
        model = HomeCollectionAppointment
        fields = '__all__'

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        if instance.home_collections:
            response_object['home_collections'] = LabRadiologyItemSerializer(
                instance.home_collections, many=True,
                context={
                    "hospital__id": instance.hospital_id
                }).data
        if instance.address:
            response_object['address'] = PatientAddressSerializer(
                instance.address).data

        if instance.family_member:
            response_object['family_member'] = FamilyMemberSerializer(
                instance.family_member,
                fields=('id', 'mobile', 'relation_name', 'uhid_number', 'display_picture',
                        'gender', 'first_name')).data

        if instance.hospital:
            response_object['hospital'] = HospitalSerializer(
                instance.hospital).data

        response_object['patient'] = PatientSerializer(
            instance.patient,
            fields=('id', 'mobile', 'uhid_number', 'first_name', 'display_picture',
                    'email', 'gender')).data

        return response_object
