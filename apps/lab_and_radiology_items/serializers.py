import logging
from django.db.models import Q
from django.utils.timezone import datetime
from rest_framework import serializers

from django.db import transaction
from apps.appointments.serializers import CancellationReasonSerializer
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

logger = logging.getLogger("django")

class LabRadiologyItemPricingSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = LabRadiologyItemPricing
        exclude = ('created_at', 'updated_at', 'id')


class LabRadiologyItemSerializer(DynamicFieldsModelSerializer):
    price = serializers.SerializerMethodField()
    is_date_expired = serializers.SerializerMethodField()
    is_added_to_cart = serializers.BooleanField(default=False,
                                                read_only=True)

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

    def get_is_date_expired(self, instance):
        if 'hospital__id' in self.context:
            hospital_id = self.context['hospital__id']
        else:
            hospital_id = self.context['request'].query_params.get(
                'hospital__id')

        return not instance.lab_radiology_item_pricing.filter(hospital_id=hospital_id).filter((Q(end_date__gte=datetime.now().date()) | Q(end_date__isnull=True)) &
                                                                                              Q(start_date__lte=datetime.now().date())).exists()


class HomeCareServiceSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = HomeCareService
        exclude = ('created_at', 'updated_at',)
    
    def to_representation(self, instance):
        response_object = super().to_representation(instance)

        try:
            if instance.image:
                response_object['image'] = generate_pre_signed_url(
                    instance.image.url)
        except Exception as error:
            logger.info("Exception in HomeCareServiceSerializer: %s"%(str(error)))
            response_object['image'] = None

        return response_object


class PatientServiceAppointmentSerializer(DynamicFieldsModelSerializer):
    patient = serializers.UUIDField(write_only=True,
                                    default=CurrentPatientUserDefault())
    is_cancellable = serializers.ReadOnlyField()

    class Meta:
        model = PatientServiceAppointment
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        appointment = PatientServiceAppointment.objects.create(**validated_data)
        address = PatientAddressSerializer(appointment.referenced_address).data
        appointment.address = address
        appointment.save()
        return appointment

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        try:
            if instance.document:
                response_object['document'] = generate_pre_signed_url(
                    instance.document.url)
        except Exception as error:
            logger.info("Exception in PatientServiceAppointmentSerializer: %s"%(str(error)))
            response_object['display_picture'] = None

        if instance.hospital:
            response_object['hospital'] = HospitalSerializer(
                instance.hospital).data

        if instance.service:
            response_object['service'] = HomeCareServiceSerializer(
                instance.service).data

        if instance.reason:
            response_object['reason'] = CancellationReasonSerializer(
                instance.reason).data['reason']

        if instance.family_member:
            response_object['family_member'] = FamilyMemberSerializer(
                instance.family_member,
                fields=('id', 'mobile', 'relation_name', 'uhid_number', 'display_picture', 'gender',
                        'first_name', 'last_name')).data

        response_object['patient'] = PatientSerializer(
            instance.patient,
            fields=('id', 'mobile', 'uhid_number', 'first_name', 'display_picture',
                    'email', 'gender', 'last_name')).data

        return response_object


class HomeCollectionAppointmentSerializer(DynamicFieldsModelSerializer):
    patient = serializers.UUIDField(write_only=True,
                                    default=CurrentPatientUserDefault())
    is_cancellable = serializers.ReadOnlyField()

    class Meta:
        model = HomeCollectionAppointment
        fields = '__all__'

    @transaction.atomic
    def create(self, validated_data):
        home_collections = validated_data.pop("home_collections")
        appointment = HomeCollectionAppointment.objects.create(**validated_data)
        appointment.home_collections.set(home_collections)
        address = PatientAddressSerializer(appointment.referenced_address).data
        appointment.address = address
        appointment.save()
        return appointment

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        if instance.home_collections:
            response_object['home_collections'] = LabRadiologyItemSerializer(
                instance.home_collections, many=True,
                context={
                    "hospital__id": instance.hospital_id
                }).data
        try:
            if instance.document:
                response_object['document'] = generate_pre_signed_url(
                    instance.document.url)
        except Exception as error:
            logger.info("Exception in HomeCollectionAppointmentSerializer: %s"%(str(error)))
            response_object['display_picture'] = None

        if instance.reason:
            response_object['reason'] = CancellationReasonSerializer(
                instance.reason).data['reason']

        if instance.family_member:
            response_object['family_member'] = FamilyMemberSerializer(
                instance.family_member,
                fields=('id', 'mobile', 'relation_name', 'uhid_number', 'display_picture',
                        'gender', 'first_name', 'last_name', 'email')).data

        if instance.hospital:
            response_object['hospital'] = HospitalSerializer(
                instance.hospital).data

        response_object['patient'] = PatientSerializer(
            instance.patient,
            fields=('id', 'mobile', 'uhid_number', 'first_name', 'display_picture',
                    'email', 'gender', 'last_name', 'email')).data

        return response_object
