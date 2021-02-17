from rest_framework import serializers
from apps.manipal_admin.models import ManipalAdmin, AdminRole, AdminMenu

class ManipalAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManipalAdmin
        fields = ['id', 'name', 'email']


class ManipalAdminResetPasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManipalAdmin
        fields = ('password',)

    extra_kwargs = {'email': {'write_only': True}}

class ManipalAdminRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminRole
        fields = '__all__'

class ManipalAdminMenuSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = AdminMenu
        fields = '__all__'