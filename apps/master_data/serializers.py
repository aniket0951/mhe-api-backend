from rest_framework import serializers
from utils.serializers import DynamicFieldsModelSerializer

from .models import Department, Hospital, Specialisation, HospitalDepartment
from django.contrib.gis.geos import Point
from django.contrib.gis.geos import fromstr
from django.contrib.gis.db.models.functions import Distance as Django_Distance

class HospitalSerializer(DynamicFieldsModelSerializer):
    distance = serializers.SerializerMethodField()

    class Meta:
        model = Hospital
        exclude = ('created_at', 'updated_at',)


    def get_distance(self, obj):
        try:
            request_data = self.context['request']
            longitude = float(request_data.query_params.get("longitude", 0))
            latitude = float(request_data.query_params.get("latitude", 0))
            user_location = Point(longitude, latitude, srid=4326)
            distance = obj.location.distance(user_location)
            return distance*100
        except Exception as e:
            print(e)
        return None
        
class SpecialisationSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Specialisation
        exclude = ('created_at', 'updated_at',)


class DepartmentSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Department
        exclude = ('created_at', 'updated_at',)
        # exclude = ('created_at', 'updated_at',)
        # fields = ('id', 'description', 'distance')



class HospitalDepartmentSerializer(DynamicFieldsModelSerializer):
    department = DepartmentSerializer()
    class Meta:
        model = HospitalDepartment
        exclude = ('created_at', 'updated_at',)
