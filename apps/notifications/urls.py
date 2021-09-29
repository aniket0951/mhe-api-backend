from django.urls import include, path

from rest_framework import routers
from rest_framework.routers import DefaultRouter

from .views import (ManagePushNotificationsViewSet, MobileDeviceViewSet, NotificationTemplateViewSet, NotificationlistView,
                    PushNotificationViewSet, ScheduleNotificationViewSet)

router = DefaultRouter(trailing_slash=False)

router.register('all_notifications', NotificationlistView)
router.register('manage_push_notification', ManagePushNotificationsViewSet)
router.register('notification_template', NotificationTemplateViewSet)
router.register('schedule_notification', ScheduleNotificationViewSet)

urlpatterns = [
    path('device', MobileDeviceViewSet.as_view()),
    path('push_notification', PushNotificationViewSet.as_view()),
    *router.urls

]
