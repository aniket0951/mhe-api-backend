from utils.serializers import DynamicFieldsModelSerializer

from .models import Department, Hospital, Specialisation


class HospitalSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Hospital
        exclude = ('created_at', 'updated_at',)


class SpecialisationSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Specialisation
        exclude = ('created_at', 'updated_at',)


class DepartmentSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Department
        exclude = ('created_at', 'updated_at',)
