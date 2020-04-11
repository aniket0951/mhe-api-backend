from datetime import datetime

from apps.doctors.models import Doctor
from apps.doctors.serializers import (DoctorSerializer,
                                      DoctorSpecificSerializer,
                                      HospitalSerializer)
from apps.health_packages.models import HealthPackagePricing
from apps.health_packages.serializers import (HealthPackagePricingSerializer,
                                              HealthPackageSpecificSerializer)
from apps.master_data.models import Hospital
from apps.patients.models import FamilyMember, Patient
from apps.patients.serializers import FamilyMemberSerializer, PatientSerializer
from rest_framework import serializers
from utils.serializers import DynamicFieldsModelSerializer

from .models import Appointment, CancellationReason, HealthPackageAppointment


class CancellationReasonSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = CancellationReason
        fields = '__all__'


class AppointmentSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = Appointment
        fields = '__all__'

    def to_representation(self, instance):
        response_object = super().to_representation(instance)

        if instance.doctor:
            response_object['doctor'] = DoctorSerializer(instance.doctor).data

        if instance.patient:
            response_object['patient'] = PatientSerializer(instance.patient).data

        if instance.family_member:
            response_object['family_member'] = FamilyMemberSerializer(instance.family_member).data

        if instance.hospital:
            response_object['hospital'] = HospitalSerializer(instance.hospital).data

        if instance.reason:
            response_object["reason"] = CancellationReasonSerializer(instance.reason).data

        return response_object


class HealthPackageAppointmentSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = HealthPackageAppointment
        fields = '__all__'


class HealthPackageAppointmentDetailSerializer(DynamicFieldsModelSerializer):
    from apps.payments.serializers import PaymentSerializer
    hospital = HospitalSerializer(read_only=True)
    payment = PaymentSerializer(read_only=True)
    health_package = HealthPackageSpecificSerializer(read_only=True)
    reason = CancellationReasonSerializer(read_only=True)
    pricing = serializers.SerializerMethodField()

    class Meta:
        model = HealthPackageAppointment
        fields = '__all__'

    def get_pricing(self, instance):
        hospital_id = instance.hospital.id
        health_package_id = instance.health_package.id
        health_package = HealthPackagePricing.objects.filter(
            health_package_id=health_package_id, hospital_id=hospital_id).first()
        return HealthPackagePricingSerializer(health_package).data
