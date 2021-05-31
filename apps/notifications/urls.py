from django.urls import include, path

from rest_framework import routers
from rest_framework.routers import DefaultRouter

from .views import (ManagePushNotificationsViewSet, MobileDeviceViewSet, NotificationlistView,
                    PushNotificationViewSet)

router = DefaultRouter(trailing_slash=False)

router.register('all_notifications', NotificationlistView)


urlpatterns = [
    path('device', MobileDeviceViewSet.as_view()),
    path('push_notification', PushNotificationViewSet.as_view()),
    path('manage_push_notification', ManagePushNotificationsViewSet.as_view()),
    *router.urls

]
