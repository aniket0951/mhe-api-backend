from manipal_api.celery import app
from pyfcm import FCMNotification
from fcm_django.models import FCMDevice
from manipal_api.settings import FCM_API_KEY

@app.task(bind=True, name="push_notifications")
def send_push_notification(self,**kwargs):
    fcm = FCMNotification(api_key=FCM_API_KEY)
    result = fcm.notify_single_device(**kwargs)




    
    


