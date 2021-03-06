import logging
from utils.utils import generate_pre_signed_url
from utils.serializers import DynamicFieldsModelSerializer

from .models import MobileDevice, MobileNotification, NotificationTemplate, ScheduleNotifications

logger = logging.getLogger('django')

class MobileNotificationSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = MobileNotification
        fields = '__all__'


class MobileDeviceSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = MobileDevice
        fields = '__all__'
       
class NotificationTemplateSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = NotificationTemplate
        fields = '__all__'
        
class ScheduleNotificationsSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = ScheduleNotifications
        fields = '__all__'

    def to_representation(self, instance):
        response_object = super().to_representation(instance)

        try:
            if instance.file:
                response_object['file'] = generate_pre_signed_url(
                    instance.file.url)
            if instance.template_id:
                response_object['template_id'] = NotificationTemplateSerializer(instance.template_id).data

        except Exception as error:
            logger.error("Exception in ScheduleNotificationsSerializer %s"%(str(error)))
            response_object['file'] = None

        return response_object
    
