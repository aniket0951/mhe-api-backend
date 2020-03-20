from apps.appointments.models import Appointment
from apps.appointments.serializers import AppointmentSerializer
from apps.health_packages.models import HealthPackage
from apps.health_packages.serializers import HealthPackageDetailSerializer
from apps.patients.models import FamilyMember, Patient
from apps.patients.serializers import FamilyMemberSerializer, PatientSerializer
from rest_framework import serializers
from utils.serializers import DynamicFieldsModelSerializer

from .models import Payment


class PaymentSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Payment
        exclude = ('raw_info_from_salucro_response', 'updated_at')

    def to_representation(self, instance):
        response_object = super().to_representation(instance)

        if response_object['appointment']:
            response_object['appointment'] = AppointmentSerializer(
                Appointment.objects.get(id=str(response_object['appointment']))).data

        if response_object['patient']:
            response_object['patient'] = PatientSerializer(
                Patient.objects.get(id=str(response_object['patient']))).data

        if response_object['uhid_family_member']:
            response_object['uhid_family_member'] = FamilyMemberSerializer(
                FamilyMember.objects.get(id=str(response_object['uhid_family_member']))).data

        if response_object['uhid_patient']:
            response_object['uhid_patient'] = PatientSerializer(
                Patient.objects.get(id=str(response_object['uhid_patient']))).data

        return response_object
