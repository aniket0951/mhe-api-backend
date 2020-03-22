from datetime import datetime

from apps.doctors.models import Doctor
from apps.doctors.serializers import (DoctorSerializer,
                                      DoctorSpecificSerializer,
                                      HospitalSerializer)
from apps.health_packages.serializers import HealthPackageSpecificSerializer
from apps.master_data.models import Hospital
from apps.patients.models import FamilyMember, Patient
from apps.patients.serializers import FamilyMemberSerializer, PatientSerializer
from apps.payments.serializers import PaymentSerializer
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

        if response_object['doctor']:
            response_object['doctor'] = DoctorSerializer(
                Doctor.objects.get(id=str(response_object['doctor']))).data

        if response_object['patient']:
            response_object['patient'] = PatientSerializer(
                Patient.objects.get(id=str(response_object['patient']))).data

        if response_object['family_member']:
            response_object['family_member'] = FamilyMemberSerializer(
                FamilyMember.objects.get(id=str(response_object['family_member']))).data

        if response_object['hospital']:
            response_object['hospital'] = HospitalSerializer(
                Hospital.objects.get(id=str(response_object['hospital']))).data

        if response_object["reason"]:
            response_object["reason"] = CancellationReasonSerializer(
                CancellationReason.objects.get(id=str(response_object['reason']))).data

        return response_object


class HealthPackageAppointmentSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = HealthPackageAppointment
        fields = '__all__'


class HealthPackageAppointmentDetailSerializer(DynamicFieldsModelSerializer):
    hospital = HospitalSerializer(read_only=True)
    payment = PaymentSerializer(read_only=True)
    health_package = HealthPackageSpecificSerializer(read_only=True)

    class Meta:
        model = HealthPackageAppointment
        fields = '__all__'
