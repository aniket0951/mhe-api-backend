from rest_framework import serializers
from apps.manipal_admin.models import ManipalAdmin

class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManipalAdmin
        fields = ['id', 'first_name', 'last_name', 'middle_name', 'email']