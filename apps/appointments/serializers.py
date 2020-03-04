import datetime
from datetime import datetime

from apps.doctors.models import Doctor
from apps.doctors.serializers import (DoctorSerializer,
                                      DoctorSpecificSerializer,
                                      HospitalSerializer)
from apps.master_data.models import Hospital
from apps.patients.models import FamilyMember, Patient
from apps.patients.serializers import FamilyMemberSerializer, PatientSerializer
from rest_framework import serializers
from utils.serializers import DynamicFieldsModelSerializer

from .models import Appointment


class AppointmentDoctorSerializer(DynamicFieldsModelSerializer):
    doctor = DoctorSpecificSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = ['doctor', 'appointment_date']


class AppointmentSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = Appointment
        fields = ('id', 'appointment_identifier', 'patient', 'family_member', 'doctor',
                  'hospital', 'appointment_date', 'appointment_slot', 'status')

    def to_representation(self, instance):
        response_object = super().to_representation(instance)

        if response_object['doctor']:
            response_object['doctor'] = DoctorSerializer(
                Doctor.objects.get(id=str(response_object['doctor']))).data

        if response_object['patient']:
            response_object['patient'] = PatientSerializer(
                Patient.objects.get(id=str(response_object['patient']))).data

        if response_object['family_member']:
            response_object['family_member'] = PatientSerializer(
                FamilyMember.objects.get(id=str(response_object['family_member']))).data

        if response_object['hospital']:
            response_object['hospital'] = HospitalSerializer(
                Hospital.objects.get(id=str(response_object['hospital']))).data

        return response_object
