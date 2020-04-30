from apps.appointments.models import Appointment
from apps.appointments.serializers import AppointmentSerializer, 
from apps.health_packages.models import HealthPackage
from apps.health_packages.serializers import HealthPackageDetailSerializer
from apps.master_data.models import Hospital
from apps.master_data.serializers import HospitalSerializer
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

        if instance.appointment:
            response_object['appointment'] = AppointmentSerializer(instance.appointment).data
        
        if instance.health_package_appointment:
            response_object['health_package_appointment'] = HealthPackageDetailSerializer(instance.health_package_appointment).data

        if instance.patient:
            response_object['patient'] = PatientSerializer(instance.patient).data

        if instance.payment_done_for_family_member:
            response_object['payment_done_for_family_member'] = FamilyMemberSerializer(instance.payment_done_for_family_member).data

        if instance.payment_done_for_patient:
            response_object['payment_done_for_patient'] = PatientSerializer(instance.payment_done_for_patient).data

        if instance.location:
            response_object['location'] = HospitalSerializer(instance.location).data

        return response_object
