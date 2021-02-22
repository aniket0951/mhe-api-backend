from rest_framework import serializers
from apps.manipal_admin.models import ManipalAdmin, AdminRole, AdminMenu
from utils.serializers import DynamicFieldsModelSerializer
from rest_framework.serializers import ValidationError
from utils.custom_validation import ValidationUtil
from phonenumber_field.serializerfields import PhoneNumberField
class ManipalAdminSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = ManipalAdmin
        fields = ['id', 'name', 'email','role', 'menus']
        
    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        all_menus = AdminMenu.objects.all()
        role_id= response_object.get('role')
        allowed_menus = response_object.get('menus')
        response_object["menu_rights"] = {}
        for menu in all_menus:
            response_object["menu_rights"][menu.name] = False
            if menu.id in allowed_menus:
                response_object["menu_rights"][menu.name] = True
        return response_object

class ManipalAdminTypeSerializer(DynamicFieldsModelSerializer):

    mobile = PhoneNumberField()
    class Meta:
        model = ManipalAdmin
        fields = ['id', 'name', 'email','role', 'menus', 'mobile']
        
    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        all_menus = AdminMenu.objects.all()
        role_id= response_object.get('role')
        allowed_menus = response_object.get('menus')
        response_object["menu_rights"] = {}
        for menu in all_menus:
            response_object["menu_rights"][menu.name] = False
            if menu.id in allowed_menus:
                response_object["menu_rights"][menu.name] = True
        return response_object

    def update(self, instance, validated_data):
        restriced_fields = [
                    'mobile',
                    'mobile_verified',
                    'email',
                ]
        validated_data = {
            k: v for k, v in validated_data.items() if not k in restriced_fields}
        validate_fields = ["name"]
        validated_fields = [ k for k, v in validated_data.items() if k in validate_fields and v and not ValidationUtil.validate_alphawidespace(v)]
        if validated_fields:
            raise ValidationError("Only alphabets are allowed for %s"%(str(validated_fields[0])))
        
        return super().update(instance, validated_data)    
    

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
        return response_object


class ManipalAdminMenuSerializer(DynamicFieldsModelSerializer):
    
    class Meta:
        model = AdminMenu
        exclude = ('created_at', 'updated_at')