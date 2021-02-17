from rest_framework import serializers
from apps.manipal_admin.models import ManipalAdmin, AdminRole, AdminMenu
from utils.serializers import DynamicFieldsModelSerializer

class ManipalAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManipalAdmin
        fields = ['id', 'name', 'email']


class ManipalAdminResetPasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManipalAdmin
        fields = ('password',)

    extra_kwargs = {'email': {'write_only': True}}

class ManipalAdminRoleSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = AdminRole
        exclude = ('created_at', 'updated_at')

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        all_menus = AdminMenu.objects.all()
        allowed_menus = response_object.get("menus")
        response_object["menu_rights"] = {}
        for menu in all_menus:
            response_object["menu_rights"][menu.name] = False
            if menu.id in allowed_menus:
                response_object["menu_rights"][menu.name] = True
        response_object.pop("menus")
        return response_object


class ManipalAdminMenuSerializer(DynamicFieldsModelSerializer):
    
    class Meta:
        model = AdminMenu
        fields = '__all__'