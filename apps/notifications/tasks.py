from manipal_api.celery import app
from pyfcm import FCMNotification
from fcm_django.models import FCMDevice
from manipal_api.settings import FCM_API_KEY
from .serializers import MobileNotificationSerializer

@app.task(bind=True, name="push_notifications")
def send_push_notification(self,**kwargs):
    notification_data = kwargs["notification_data"]
    fcm = FCMNotification(api_key=FCM_API_KEY)
    mobile_notification_serializer = MobileNotificationSerializer(
                data=notification_data)
    mobile_notification_serializer.is_valid(raise_exception=True)
    notification_instance = mobile_notification_serializer.save()
    if notification_instance.recipient.device.token:
        result = fcm.notify_single_device(registration_id=notification_instance.recipient.device.token, data_message={
                                        "title": notification_instance.title, "message": notification_instance.message}, low_priority=False)




    
    


