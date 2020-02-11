from .models import Appointment
from rest_framework import serializers
from apps.doctors.serializers import DoctorSerializer, DoctorSpecificSerializer, PatientSpecificSerializer, HospitalSpecificSerializer
from apps.patients.serializers import PatientSerializer
from apps.doctors.models import Doctor
from apps.master_data.models import Hospital
from apps.patients.models import Patient

class AppointmentDoctorSerializer(serializers.ModelSerializer):
    doctor = DoctorSpecificSerializer(read_only=True)

    class Meta:
        model  = Appointment
        fields  =  ['doctor']



class AppointmentSerializer(serializers.ModelSerializer):
    doctor = DoctorSpecificSerializer(read_only=True)
    patient = PatientSpecificSerializer(read_only = True)
    hospital = HospitalSpecificSerializer(read_only = True)
    class Meta:
        model = Appointment
        fields = ('id','patient', 'token_no' , 'doctor' , 'hospital' ,'time_slot_from' , 'appointment_date', 'status')
    
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

    