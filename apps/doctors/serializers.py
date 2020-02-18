from rest_framework import serializers

from apps.doctors.models import Doctor
from apps.master_data.models import Department, Hospital
from apps.patients.models import Patient


class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = '__all__'


class HospitalDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = '__all__'


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['code']


class DepartmentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'


class DoctorSerializer(serializers.ModelSerializer):
    linked_hospitals = HospitalSerializer(read_only=True, many=True)
    specialisations = DepartmentSerializer(read_only=True, many=True)

    class Meta:
        model = Doctor
        fields = ['code', 'id', 'first_name', 'experience', 'linked_hospitals', 'specialisations',
                  'designation', 'awards_and_achievements', 'start_date', 'end_date', 'profile_image']


class DoctorSpecificSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ['id', 'first_name', 'experience']


class HospitalSpecificSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ['id']


class PatientSpecificSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['id']
