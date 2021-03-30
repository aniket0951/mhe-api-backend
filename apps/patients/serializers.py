
from apps.patients.constants import PatientsConstants
import logging

from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework.serializers import ValidationError
from apps.master_data.models import Hospital
from apps.master_data.serializers import HospitalSerializer, CompanySerializer
from apps.patient_registration.serializers import RelationSerializer
from rest_framework import serializers
from utils.serializers import DynamicFieldsModelSerializer
from utils.utils import generate_pre_signed_url,assign_users
from utils.custom_validation import ValidationUtil

from .models import CovidVaccinationRegistration, FamilyMember, Patient, PatientAddress, WhiteListedToken

logger = logging.getLogger("django")

class PatientSerializer(DynamicFieldsModelSerializer):
    mobile = PhoneNumberField()
    family_members_count = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        exclude = (
                'is_staff', 
                'is_superuser', 
                'user_permissions', 
                'groups', 

                'password',
                'otp_expiration_time',

                'email_otp',
                "email_otp_expiration_time",
                
                "new_mobile_verification_otp",
                "new_mobile_otp_expiration_time",

                'corporate_email_otp',
                'corporate_email_otp_expiration_time'
            )

        read_only_fields = (
                    'id',
                    'last_login',
                    'created_at',
                    'updated_at',
                    'is_active',
                    'mobile_verified',
                    'is_corporate'
                )

        extra_kwargs = {
            # 'password': {'write_only': True,
            #                          "error_messages": {"required": "Enter your password."}},
            # 'mobile': {"error_messages": {"required": "Mobile number is mandatory to create your account."}},
            'facebook_id'   : {'write_only': True, },
            'google_id'     : {'write_only': True, },
            'first_name'    : {"error_messages": {"required": "First name is mandatory to create your account."}},
            'email'         : {"error_messages": {"required": "Email is mandatory to create your account."}}
        }

    def get_family_members_count(self, instance):
        return FamilyMember.objects.filter(patient_info__id=instance.id,
                                           is_visible=True).count()

    def to_internal_value(self, data):
        restriced_fields = [
                            'groups', 
                            'user_permissions', 

                            'pre_registration_number',

                            'is_staff',
                            'is_visible', 
                            'is_superuser',
                            'raw_info_from_manipal_API', 

                            'password',
                            'otp_expiration_time',
                            
                            'email_otp',
                            'email_verified',
                            'email_otp_expiration_time',

                            'mobile_verified',

                            "new_mobile_verification_otp",
                            "new_mobile_otp_expiration_time",

                            "is_corporate",
                            'corporate_email_otp',
                            'corporate_email_otp_expiration_time'
                        ]
        data = {
            k: v for k, v in data.items() if not k in restriced_fields}
        return super().to_internal_value(data)

    def to_representation(self, instance):
        response_object = super().to_representation(instance)

        if 'favorite_hospital' in response_object and response_object['favorite_hospital']:
            response_object['favorite_hospital'] = HospitalSerializer(
                Hospital.objects.get(id=str(response_object['favorite_hospital']))).data

        try:
            response_object['display_picture'] = generate_pre_signed_url(instance.display_picture.url)
        except Exception as error:
            logger.info("Exception in PatientSerializer: %s"%(str(error)))
            response_object['display_picture'] = None

        if instance.company_info:
            response_object['company_info'] = CompanySerializer(instance.company_info).data

        return response_object

    def create(self, validated_data):
        restriced_fields = ['uhid_number', 'mobile_verified', 'email_verified']
        validated_data = {
            k: v for k, v in validated_data.items() if not k in restriced_fields}
        validate_fields = ["first_name","last_name","middle_name"]
        validated_fields = [ k for k, v in validated_data.items() if k in validate_fields and v and not ValidationUtil.validate_text_only(v)]
        if validated_fields:
            raise ValidationError(PatientsConstants.NO_SPECIAL_ONLY_ALPHABETS%(str(validated_fields[0])))
        return super().create(validated_data)

    def update(self, instance, validated_data):
        restriced_fields = [
                    'is_active',
                    'is_corporate',

                    'mobile',
                    'mobile_verified',

                    'uhid_number',

                    'otp_expiration_time',
                    'email_otp_expiration_time',
                    "new_mobile_otp_expiration_time",
                    'corporate_email_otp_expiration_time',
                ]
        validated_data = {
            k: v for k, v in validated_data.items() if not k in restriced_fields}
        validate_fields = ["first_name","last_name","middle_name"]
        validated_fields = [ k for k, v in validated_data.items() if k in validate_fields and v and not ValidationUtil.validate_text_only(v)]
        if validated_fields:
            raise ValidationError(PatientsConstants.NO_SPECIAL_ONLY_ALPHABETS%(str(validated_fields[0])))
        
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
        exclude = (
                'raw_info_from_manipal_API', 
                'mobile_verification_otp',
                'mobile_otp_expiration_time', 
        )
        extra_kwargs = {
            'relation_name': {"error_messages":
                              {"required": "Enter your relationship with the person whom you are linking."}}}

    def create(self, validated_data):
        restriced_fields = ['uhid_number']
        validated_data = {
            k: v for k, v in validated_data.items() if not k in restriced_fields}
        validate_fields = ["first_name","last_name","middle_name"]
        validated_fields = [ k for k, v in validated_data.items() if k in validate_fields and v and not ValidationUtil.validate_text_only(v)]
        if validated_fields:
            raise ValidationError(PatientsConstants.NO_SPECIAL_ONLY_ALPHABETS%(str(validated_fields[0])))
        return super().create(validated_data)

    def update(self, instance, validated_data):
        restriced_fields = [
                        'uhid_number', 
                        'is_visible',

                        'mobile_verified',
                        'mobile_otp_expiration_time',

                        'email_verified',
                        'email_otp_expiration_time'
                    ]
        # 'otp_expiration_time', 'email_otp_expiration_time']
        validated_data = {
            k: v for k, v in validated_data.items() if not k in restriced_fields}
        validate_fields = ["first_name","last_name","middle_name"]
        validated_fields = [ k for k, v in validated_data.items() if k in validate_fields and v and not ValidationUtil.validate_text_only(v)]
        if validated_fields:
            raise ValidationError(PatientsConstants.NO_SPECIAL_ONLY_ALPHABETS%(str(validated_fields[0])))
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        response_object = super().to_representation(instance)

        if instance.relationship:
            response_object['relationship'] = RelationSerializer(instance.relationship).data
        try:
            response_object['display_picture'] = generate_pre_signed_url(instance.display_picture.url)
        except Exception as error:
            logger.info("Exception in FamilyMemberSerializer: %s"%(str(error)))
            response_object['display_picture'] = None

        return response_object

    def to_internal_value(self, data):
        if (not self.context['request'].method == 'POST') and 'mobile' in data:
            data.pop('mobile')
        return super().to_internal_value(data)

class PatientAddressSerializer(DynamicFieldsModelSerializer):
    patient_info = serializers.UUIDField(write_only=True, default=CurrentPatientUserDefault())

    class Meta:
        model = PatientAddress
        exclude = ('created_at', 'updated_at',)

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


class PatientSpecificSerializer(DynamicFieldsModelSerializer):
    mobile = PhoneNumberField()

    class Meta:
        model = Patient
        exclude = ('is_staff', 'is_superuser', 'otp_expiration_time',
                   'user_permissions', 'groups', 'password')


class FamilyMemberSpecificSerializer(DynamicFieldsModelSerializer):
    mobile = PhoneNumberField()
    patient_info = serializers.UUIDField(write_only=True,
                                         default=CurrentPatientUserDefault())

    class Meta:
        model = FamilyMember
        exclude = ('raw_info_from_manipal_API', 'mobile_verification_otp',
                   'email_verification_otp', 'mobile_otp_expiration_time', 'email_otp_expiration_time',
                   'created_at', 'updated_at')

class WhiteListedTokenSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = WhiteListedToken
        fields = '__all__'

class CovidVaccinationRegistrationSerializer(DynamicFieldsModelSerializer):
    
    class Meta:
        model = CovidVaccinationRegistration
        exclude = ('created_at', 'updated_at')

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        user_object = None
        
        if 'preferred_hospital' in response_object and response_object.get('preferred_hospital'):
            response_object['preferred_hospital'] = HospitalSerializer(Hospital.objects.get(id=str(response_object['preferred_hospital']))).data
            
        if 'family_member' in response_object and response_object.get('family_member'):
            user_object = FamilyMember.objects.filter(id=response_object['family_member']).first()
            response_object['family_member'] = FamilyMemberSerializer(FamilyMember.objects.get(id=str(response_object['family_member']))).data

        elif response_object['patient']:
            user_object = Patient.objects.filter(id=response_object['patient']).first()

        if user_object:
            response_object['uhid_number']      = user_object.uhid_number
            response_object['dob']              = user_object.dob
            response_object['name']             = "%s %s"%(str(user_object.first_name),str(user_object.last_name))
            response_object['mobile_number']    = "%s"%(str(user_object.mobile))
            response_object['aadhar_number']    = user_object.aadhar_number
        
        if 'patient' in response_object and response_object.get('patient'):
            response_object['patient'] = PatientSerializer(Patient.objects.get(id=str(response_object['patient']))).data

        return response_object

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)