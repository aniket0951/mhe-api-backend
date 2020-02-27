from utils.serializers import DynamicFieldsModelSerializer

from .models import Hospital


class HospitalSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Hospital
        exclude = ('created_at', 'updated_at',)
