from apps.master_data.models import Specialisation
from rest_framework import serializers
from rest_framework.serializers import ValidationError
from utils.serializers import DynamicFieldsModelSerializer

from .models import HealthPackage, HealthPackagePricing, HealthTest


class HealthTestSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = HealthTest
        exclude = ('created_at', 'updated_at',
                   'billing_sub_group', 'billing_group')


class HealthPackagePricingSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = HealthPackagePricing
        exclude = ('created_at', 'updated_at',)


class HealthPackageDetailSerializer(DynamicFieldsModelSerializer):
    included_health_tests = HealthTestSerializer(many=True)
    pricing = serializers.SerializerMethodField()
    included_health_tests_count = serializers.SerializerMethodField()

    class Meta:
        model = HealthPackage
        exclude = ('created_at', 'updated_at',)

    def get_pricing(self, instance):
        hospital_id = self.context['request'].query_params.get('hospital__id')
        return HealthPackagePricingSerializer(instance.health_package_pricing.get(hospital_id=hospital_id)).data

    def get_included_health_tests_count(self, instance):
        return instance.included_health_tests.count()


class HealthPackageSerializer(DynamicFieldsModelSerializer):
    pricing = serializers.SerializerMethodField()
    included_health_tests_count = serializers.SerializerMethodField()

    class Meta:
        model = HealthPackage
        exclude = ('created_at', 'updated_at', 'included_health_tests')

    def get_pricing(self, instance):
        if 'hospital__id' in self.context:
            hospital_id = self.context['hospital__id']
        else:
            hospital_id = self.context['request'].query_params.get(
                'hospital__id')
        return HealthPackagePricingSerializer(instance.health_package_pricing.get(hospital_id=hospital_id)).data

    def get_included_health_tests_count(self, instance):
        return instance.included_health_tests.count()


class HealthPackageSpecialisationDetailSerializer(DynamicFieldsModelSerializer):
    packages = serializers.SerializerMethodField()

    class Meta:
        model = Specialisation
        exclude = ('created_at', 'updated_at',)

    def get_packages(self, instance):
        hospital_id = self.context['request'].query_params.get('hospital__id')
        if not hospital_id:
            raise ValidationError("Hospital ID is missiing!")

        hospital_related_health_packages = HealthPackagePricing.objects.filter(
            hospital=hospital_id).values_list('health_package_id', flat=True)

        return HealthPackageSerializer(instance.health_package.filter(id__in=hospital_related_health_packages), many=True,
                                       context=self.context).data


class HealthPackageSpecialisationSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = Specialisation
        exclude = ('created_at', 'updated_at',)


class HealthPackageSpecificSerializer(DynamicFieldsModelSerializer):
    included_health_tests = HealthTestSerializer(many=True)

    class Meta:
        model = HealthPackage
        fields = '__all__'
