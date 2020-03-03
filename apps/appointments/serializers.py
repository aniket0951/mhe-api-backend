from apps.doctors.models import Doctor
from apps.doctors.serializers import (DoctorSerializer,
                                      DoctorSpecificSerializer,
                                      HospitalSerializer)
from apps.master_data.models import Hospital
from apps.patients.models import Patient
from apps.patients.serializers import PatientSerializer, FamilyMemberSerializer
from rest_framework import serializers

from .models import Appointment
import datetime
from datetime import datetime


class AppointmentDoctorSerializer(serializers.ModelSerializer):
    doctor = DoctorSpecificSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = ['doctor', 'appointment_date']


class AppointmentSerializer(serializers.ModelSerializer):
    doctor = DoctorSerializer(read_only=True)
    hospital = HospitalSerializer(read_only=True)
    patient = PatientSerializer(read_only=True)
    family_member = FamilyMemberSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = ('id', 'appointmentIdentifier', 'patient', 'family_member','doctor',
                  'hospital', 'appointment_date', 'appointment_date', 'status')
