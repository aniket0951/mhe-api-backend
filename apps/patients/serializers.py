from uuid import UUID

from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from apps.master_data.models import Hospital
from apps.master_data.serializers import HospitalSerializer
from utils.serializers import DynamicFieldsModelSerializer
from utils.utils import generate_pre_signed_url, patient_user_object

from .models import FamilyMember, Patient, PatientAddress


class PatientSerializer(DynamicFieldsModelSerializer):
    mobile = PhoneNumberField()

    class Meta:
        model = Patient
        exclude = ('is_staff', 'is_superuser', 'otp_expiration_time',
                   'user_permissions', 'groups', 'password')

        read_only_fields = ('id', 'last_login', 'created_at', 'updated_at',
                            'is_active', 'mobile_verified',
                            )

        extra_kwargs = {
            # 'password': {'write_only': True,
            #                          "error_messages": {"required": "Enter your password."}},
            # 'mobile': {"error_messages": {"required": "Mobile number is mandatory to create your account."}},
            'facebook_id': {'write_only': True, },
            'google_id': {'write_only': True, },
            'first_name': {"error_messages": {"required": "First name is mandatory to create your account."}},
            'email': {"error_messages": {"required": "Email is mandatory to create your account."}}
        }

    def to_representation(self, instance):
        response_object = super().to_representation(instance)

        if response_object['favorite_hospital']:
            response_object['favorite_hospital'] = HospitalSerializer(
                Hospital.objects.get(id=str(response_object['favorite_hospital']))).data

        try:
            response_object['display_picture'] = generate_pre_signed_url(
                instance.display_picture.url)
        except Exception as error:
            print(error)
            response_object['display_picture'] = None

        return response_object

    def create(self, validated_data):
        # TODO: Writable but not updatable
        if 'uhid_number' in validated_data:
            _ = validated_data.pop('uhid_number')
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # TODO: Writable but not updatable
        if 'mobile' in validated_data:
            _ = validated_data.pop('mobile')
        # TODO: Writable but not updatable
        if 'uhid_number' in validated_data:
            _ = validated_data.pop('uhid_number')
        return super().update(instance, validated_data)


class CurrentPatientUserDefault:
    """
    May be applied as a `default=...` value on a serializer field.
    Returns the current user.
    """
    requires_context = True

    def __call__(self, serializer_field):
        return Patient.objects.get(id=serializer_field.context['request'].user.id)


class FamilyMemberSerializer(DynamicFieldsModelSerializer):
    mobile = PhoneNumberField()
    patient_info = serializers.UUIDField(write_only=True,
                                         default=CurrentPatientUserDefault())

    class Meta:
        model = FamilyMember
        exclude = ('raw_info_from_manipal_API', 'mobile_verification_otp',
                   'email_verification_otp', 'mobile_otp_expiration_time', 'email_otp_expiration_time',
                   'created_at', 'updated_at')

        extra_kwargs = {
            'relation_name': {"error_messages":
                              {"required": "Enter your relationship with the person whom you are linking."}}}

    def create(self, validated_data):
        if 'uhid_number' in validated_data:
            validated_data.pop('uhid_number')
        return super().create(validated_data)

    def to_representation(self, instance):
        response_object = super().to_representation(instance)

        try:
            response_object['display_picture'] = generate_pre_signed_url(
                instance.display_picture.url)
        except Exception as error:
            print(error)
            response_object['display_picture'] = None

        return response_object




class PatientAddressSerializer(DynamicFieldsModelSerializer):
    patient_info = serializers.UUIDField(write_only=True,
                                         default=CurrentPatientUserDefault())

    class Meta:
        model = PatientAddress
        fields = '__all__'

        extra_kwargs = {
            'pincode_number': {"error_messages": {"required": "Enter your pin code."}},
            'house_details': {"error_messages": {"required": "House number is mandatory to add address."}},
            'area_details': {"error_messages": {"required": "Area/landmark details are mandatory to add address."}},
        }

    def to_representation(self, instance):
        obj = super().to_representation(instance)
        if instance.location:
            obj['longitude'] = instance.location.x
            obj['latitude'] = instance.location.y
        return obj
