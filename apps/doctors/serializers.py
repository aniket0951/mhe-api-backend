from rest_framework import serializers
from apps.doctors.models import Doctor
from apps.master_data.models import Hospital, Specialisation

class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ['id', 'code', 'profit_center', 'description', 'email', 'mobile', 'address']


class SpecialisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialisation
        fields = ['id', 'code', 'description', 'start_date', 'end_date']



class DoctorSerializer(serializers.ModelSerializer):
    linked_hospitals = HospitalSerializer(read_only=True, many=True)
    specialisations = SpecialisationSerializer(read_only=True, many=True)
    class Meta:
        model = Doctor
        fields = ['id', 'code', 'linked_hospitals', 'specialisations', 'designation', 'awards_and_achievements', 'experience', 'start_date', 'end_date']
