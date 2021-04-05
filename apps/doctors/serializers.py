from apps.master_data.serializers import HospitalDepartmentSerializer
from apps.doctors.models import Doctor, DoctorCharges
from apps.master_data.models import (Department, Hospital, HospitalDepartment,
                                     Specialisation)
from apps.patients.models import Patient
from rest_framework import serializers
from utils.serializers import DynamicFieldsModelSerializer
from rest_framework.test import APIClient

import json
client = APIClient()

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
        exclude = ('password', 'last_login', 'is_superuser', 'updated_at',
                   'created_at', 'is_staff', 'is_active', 'groups', 'user_permissions')

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        if instance.name:
            response_object['name'] = instance.name.title()
        response_object["consultation_charge"] = None
        doctor_consultation = DoctorCharges.objects.filter(doctor_info=instance.id)
        if not doctor_consultation:
            DoctorChargesSerializer.get_and_update_doctor_price(instance)
            doctor_consultation = DoctorCharges.objects.filter(doctor_info=instance.id)
        if doctor_consultation:
            response_object["consultation_charge"] = DoctorChargesSerializer(doctor_consultation, many=True).data
        return response_object


class DoctorSpecificSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Doctor
        fields = ['id', 'name', 'experience']


class DoctorChargesSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = DoctorCharges
        fields = '__all__'

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        if instance.department_info:
            response_object['department_code'] = instance.department_info.code
            response_object['department_name'] = instance.department_info.name
            if instance.doctor_info and instance.doctor_info.hospital_departments:
                response_object['hospital_department_details'] = HospitalDepartmentSerializer(instance.doctor_info.hospital_departments.filter(department__id=instance.department_info.id).first(), many = False).data
            
        return response_object

    @staticmethod
    def get_and_update_doctor_price(doctor_instance):
    
        all_departments = doctor_instance.hospital_departments.all()

        for each_department in all_departments:
            
            data = dict()
            location_code = doctor_instance.hospital.code
            doctor_code = doctor_instance.code
            data["doctor_info"] = doctor_instance.id
            data["department_info"] = each_department.department.id

            try:
                response = client.post('/api/doctors/doctor_charges',json.dumps({
                                                        'location_code': location_code, 
                                                        'specialty_code': each_department.department.code, 
                                                        'doctor_code': doctor_code
                                                    }), content_type='application/json')

                consultation_charge = response.data["data"]

                if response.status_code == 200 and response.data["success"] == True:
                    data["hv_consultation_charges"] = consultation_charge["hv_charge"]
                    data["vc_consultation_charges"] = consultation_charge["vc_charge"]
                    data["pr_consultation_charges"] = consultation_charge["pr_charge"]

                    doctor_instance = DoctorCharges.objects.filter(doctor_info__code=doctor_code, department_info__code=each_department.department.code).first()
                    if doctor_instance:
                        serializer = DoctorChargesSerializer(doctor_instance, data=data, partial=True)
                    else:
                        serializer = DoctorChargesSerializer(data=data)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()

            except Exception as e:
                print("Unexpected error occurred while calling the API- {0}".format(e))
