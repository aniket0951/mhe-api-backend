from apps.doctors.models import Doctor
from apps.master_data.models import (Department, Hospital, HospitalDepartment,
                                     Specialisation)
from apps.patients.models import Patient
from rest_framework import serializers


class DepartmentSpecificSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'


class SpecialisationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Specialisation
        fields = '__all__'


class HospitalSerializer(serializers.ModelSerializer):

    class Meta:
        model = Hospital
        fields = '__all__'




class DepartmentSerializer(serializers.ModelSerializer):
    hospital = HospitalSerializer()
    department = DepartmentSpecificSerializer()

    class Meta:
        model = HospitalDepartment
        fields = '__all__'


class DoctorSerializer(serializers.ModelSerializer):
    hospital_departments = DepartmentSerializer(many=True)
    specialisations = SpecialisationSerializer(many=True)

    class Meta:
        model = Doctor
        fields = ['id', 'code', 'name', 'hospital', 'hospital_departments',
                  'specialisations', 'qualification', 'educational_degrees', 'experience']


class DoctorSpecificSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ['id', 'name', 'experience']


