from .models import LabRadiologyItem, LabRadiologyItemPricing
from utils.serializers import DynamicFieldsModelSerializer
from rest_framework import serializers


class LabRadiologyItemPricingSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = LabRadiologyItemPricing
        exclude = ('created_at', 'updated_at', 'id')


class LabRadiologyItemSerializer(DynamicFieldsModelSerializer):
    price = serializers.SerializerMethodField()

    class Meta:
        model = LabRadiologyItem
        exclude = ('created_at', 'updated_at',
                   'billing_sub_group', 'billing_group')

    def get_price(self, instance):
        hospital_id = self.context['request'].query_params.get('hospital__id')
        return instance.labradiologyitempricing_set.get(hospital_id=hospital_id).price
