from utils.serializers import DynamicFieldsModelSerializer

from .models import MobileDevice, MobileNotification


class MobileNotificationSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = MobileNotification
        fields = '__all__'


class MobileDeviceSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = MobileDevice
        fields = '__all__'
