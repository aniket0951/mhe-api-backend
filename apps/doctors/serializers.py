from rest_framework import serializers
from apps.doctors.models import Doctor
from apps.master_data.models import Hospital, Specialisation
from apps.patients.models import Patient

class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ['profit_center']

class HospitalDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = '__all__'


class SpecialisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialisation
        fields = ['code']

class SpecialisationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialisation
        fields = '__all__'



class DoctorSerializer(serializers.ModelSerializer):
    linked_hospitals = HospitalSerializer(read_only=True, many=True)
    specialisations = SpecialisationSerializer(read_only=True, many=True)
    class Meta:
        model = Doctor
        fields = ['first_name' ,'linked_hospitals', 'specialisations', 'designation', 'awards_and_achievements', 'start_date', 'end_date']


class DoctorSpecificSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ['id']

class HospitalSpecificSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ['id']

class PatientSpecificSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['id']
