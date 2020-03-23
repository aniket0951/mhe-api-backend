from rest_framework import serializers
from apps.manipal_admin.models import ManipalAdmin


class ManipalAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManipalAdmin
        fields = ['id', 'name', 'email']


class ManipalAdminResetPasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManipalAdmin
        fields = ('password',)

    extra_kwargs = {'email': {'write_only': True}}
