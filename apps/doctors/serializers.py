from apps.master_data.serializers import HospitalDepartmentSerializer
from apps.doctors.models import Doctor, DoctorCharges
from apps.master_data.models import (Department, Hospital, HospitalDepartment, Specialisation)
from apps.master_data.models import Company
from utils.serializers import DynamicFieldsModelSerializer
from rest_framework.test import APIClient
from datetime import datetime
import logging
import json
client = APIClient()
_logger = logging.getLogger("django")

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
        today_date = datetime.now().date()
        if not doctor_consultation or doctor_consultation.first().updated_at.date()<today_date:
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
    def get_promo_code(doctor_instance):
        promo_code = ""
        if doctor_instance.hospital:
            company = Company.objects.filter(hospital_info__id=doctor_instance.hospital.id).first()
            _logger.error("Company- {0}".format(str(company)))
            _logger.error("Company Promo- {0}".format(str(company.promo_code)))
            if company and company.promo_code:
                promo_code = company.promo_code
        return promo_code

    @staticmethod
    def get_doctor_price_from_mainpal(doctor_instance,department):
        consultation_charge = None
        try:
            doctor_code     = doctor_instance.code
            location_code   = doctor_instance.hospital.code
            promo_code = DoctorChargesSerializer.get_promo_code(doctor_instance)
        
            response        = client.post('/api/doctors/doctor_charges',json.dumps({
                                                            'location_code': location_code, 
                                                            'specialty_code': department.code, 
                                                            'doctor_code': doctor_code,
                                                            'promo_code':promo_code
                                                        }), content_type='application/json')
            if response.status_code == 200 and response.data["success"] == True:
                consultation_charge = response.data["data"]
        except Exception as e:
            _logger.error("Unexpected error occurred while calling the API- {0}".format(e))
        return consultation_charge


    @staticmethod
    def get_and_update_doctor_price(doctor_instance):
    
        all_departments = doctor_instance.hospital_departments.all()

        for each_department in all_departments:
            
            data = dict()
            
            doctor_code         = doctor_instance.code
            data["doctor_info"] = doctor_instance.id
            data["department_info"] = each_department.department.id

            try:
                consultation_charge = DoctorChargesSerializer.get_doctor_price_from_mainpal(doctor_instance,each_department.department)
                if consultation_charge:

                    data["hv_consultation_charges"] = consultation_charge["hv_charge"]
                    data["vc_consultation_charges"] = consultation_charge["vc_charge"]
                    data["pr_consultation_charges"] = consultation_charge["pr_charge"]
                    data["plan_code"]               = consultation_charge["plan_code"]

                    doctor_instance = DoctorCharges.objects.filter(doctor_info__code=doctor_code, department_info__code=each_department.department.code).first()
                    if doctor_instance:
                        serializer = DoctorChargesSerializer(doctor_instance, data=data, partial=True)
                    else:
                        serializer = DoctorChargesSerializer(data=data)
                        
                    serializer.is_valid(raise_exception=True)
                    serializer.save()

            except Exception as e:
                _logger.error("Unexpected error occurred while processing the API response- {0}".format(e))
