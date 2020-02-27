from apps.doctors.models import Doctor
from apps.doctors.serializers import (DoctorSerializer,
                                      DoctorSpecificSerializer,
                                      HospitalDetailSerializer,
                                      PatientSpecificSerializer)
from apps.master_data.models import Hospital
from apps.patients.models import Patient
from apps.users.serializers import UserSerializer
from rest_framework import serializers

from .models import Appointment


class AppointmentDoctorSerializer(serializers.ModelSerializer):
    doctor = DoctorSpecificSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = ['doctor']


class AppointmentSerializer(serializers.ModelSerializer):
    doctor = DoctorSerializer(read_only=True)
    hospital = HospitalDetailSerializer(read_only=True)
    req_patient = UserSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = ('id', 'appointmentIdentifier', 'req_patient', 'doctor',
                  'hospital', 'time_slot_from', 'appointment_date', 'status')

    """
    def create(self, validated_data):
        hospital_data = validated_data['hospital']
        doctor_data = validated_data['doctor']
        patient_data = validated_data.pop['patient']
        appointment = Appointment.objects.create(**validated_data)
        Hospital.objects.create(appointment=appointment, **hospital_data)
        Doctor.objects.create(appointment=appointment, **doctor_data)
        Patient.objects.create(appointment=appointment, **patient_data)
        return appointment
    """
