from django.db.models import Q
from django.utils.timezone import datetime
from rest_framework import serializers
from rest_framework.serializers import ValidationError

from apps.master_data.models import Specialisation
from utils.serializers import DynamicFieldsModelSerializer

from .models import HealthPackage, HealthPackagePricing, HealthTest


class HealthTestSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = HealthTest
        exclude = ('created_at', 'updated_at',
                   'billing_sub_group', 'billing_group')

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        if instance.description:
            response_object['description'] = instance.description.title()
        return response_object


class HealthPackagePricingSerializer(DynamicFieldsModelSerializer):
    is_discount_applicable = serializers.SerializerMethodField()
    final_price = serializers.SerializerMethodField()

    class Meta:
        model = HealthPackagePricing
        exclude = ('created_at', 'updated_at',)

    def get_is_discount_applicable(self, instance):
        if instance.discount_percentage and instance.discount_start_date < datetime.now().date() and \
                (not instance.discount_end_date or instance.discount_end_date > datetime.now().date()):
            return True
        return False

    def get_final_price(self, instance):
        return round((100 - instance.discount_percentage) * instance.price / 100)


class HealthPackageDetailSerializer(DynamicFieldsModelSerializer):
    included_health_tests = serializers.SerializerMethodField()
    pricing = serializers.SerializerMethodField()
    included_health_tests_count = serializers.SerializerMethodField()
    is_date_expired = serializers.SerializerMethodField()
    is_added_to_cart = serializers.BooleanField(default=False,
                                                read_only=True)

    class Meta:
        model = HealthPackage
        exclude = ('created_at', 'updated_at',)

    def get_pricing(self, instance):
        if 'hospital__id' in self.context:
            hospital_id = self.context['hospital__id']
        else:
            hospital_id = self.context['request'].query_params.get(
                'hospital__id')
        return HealthPackagePricingSerializer(instance.health_package_pricing.get(hospital_id=hospital_id)).data

    def get_included_health_tests_count(self, instance):
        return instance.included_health_tests.count()

    def get_is_date_expired(self, instance):
        if 'hospital__id' in self.context:
            hospital_id = self.context['hospital__id']
        else:
            hospital_id = self.context['request'].query_params.get(
                'hospital__id')

        return not instance.health_package_pricing.filter(hospital_id=hospital_id).filter((Q(end_date__gte=datetime.now().date()) | Q(end_date__isnull=True)) &
                                                                                          Q(start_date__lte=datetime.now().date())).exists()

    def get_included_health_tests(self, instance):
        health_tests = instance.included_health_tests.all().order_by('description')
        return HealthTestSerializer(health_tests, many=True).data

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        if instance.name:
            response_object['name'] = instance.name.title()
        
        try:
            if instance.image:
                response_object['image'] = generate_pre_signed_url(
                    instance.image.url)
        except Exception as error:
            response_object['image'] = None

        return response_object


class HealthPackageSerializer(DynamicFieldsModelSerializer):
    pricing = serializers.SerializerMethodField()
    included_health_tests_count = serializers.SerializerMethodField()
    is_date_expired = serializers.SerializerMethodField()
    is_added_to_cart = serializers.BooleanField(default=False,
                                                read_only=True)

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

    def get_is_date_expired(self, instance):
        if 'hospital__id' in self.context:
            hospital_id = self.context['hospital__id']
        else:
            hospital_id = self.context['request'].query_params.get(
                'hospital__id')

        return not instance.health_package_pricing.filter(hospital_id=hospital_id).filter((Q(end_date__gte=datetime.now().date()) | Q(end_date__isnull=True)) &
                                                                                          Q(start_date__lte=datetime.now().date())).exists()

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        if instance.name:
            response_object['name'] = instance.name.title()

        try:
            if instance.image:
                response_object['image'] = generate_pre_signed_url(
                    instance.image.url)
        except Exception as error:
            response_object['image'] = None

        return response_object


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

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        if instance.description:
            response_object['description'] = instance.description.title()
        return response_object


class HealthPackageSpecialisationSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = Specialisation
        exclude = ('created_at', 'updated_at',)
    
    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        if instance.description:
            response_object['description'] = instance.description.title()
        return response_object

    


class HealthPackageSpecificSerializer(DynamicFieldsModelSerializer):
    included_health_tests = HealthTestSerializer(many=True)
    included_health_tests_count = serializers.SerializerMethodField()
    pricing = serializers.SerializerMethodField()

    class Meta:
        model = HealthPackage
        fields = '__all__'

    def get_pricing(self, instance):
        hospital_id = self.context["hospital"].id
        return HealthPackagePricingSerializer(instance.health_package_pricing.get(hospital_id=hospital_id)).data

    def get_included_health_tests_count(self, instance):
        return instance.included_health_tests.count()

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        if instance.name:
            response_object['name'] = instance.name.title()
        
        try:
            if instance.image:
                response_object['image'] = generate_pre_signed_url(
                    instance.image.url)
        except Exception as error:
            response_object['image'] = None

        return response_object
