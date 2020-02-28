from rest_framework import serializers
from apps.manipal_admin.models import ManipalAdmin


class ManipalAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManipalAdmin
        fields = ['id', 'name', 'email']
