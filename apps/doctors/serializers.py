from apps.doctors.models import Doctor
from apps.master_data.models import (Department, Hospital, HospitalDepartment,
                                     Specialisation)
from apps.patients.models import Patient
from rest_framework import serializers
from utils.serializers import DynamicFieldsModelSerializer


class DepartmentSpecificSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'


class SpecialisationSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = Specialisation
        fields = '__all__'


class HospitalSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = Hospital
        fields = '__all__'


class DepartmentSerializer(DynamicFieldsModelSerializer):
    hospital = HospitalSerializer()
    department = DepartmentSpecificSerializer()

    class Meta:
        model = HospitalDepartment
        fields = '__all__'


class DoctorSerializer(DynamicFieldsModelSerializer):
    hospital_departments = DepartmentSerializer(many=True)
    specialisations = SpecialisationSerializer(many=True)

    class Meta:
        model = Doctor
        fields = '__all__'


class DoctorSpecificSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Doctor
        fields = ['id', 'name', 'experience']
