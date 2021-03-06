from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import DashboardBannerViewSet, DashboardAPIView, FAQDataViewSet, FAQDataAPIView, FlyerImagesViewSet, FlyerSchedulerViewSet, HomeCareDashboardAPIView, IOSVersionCheck, RemoveAccountAPIView, RemoveUHIDAPIView

app_name = 'dashboard'

router = DefaultRouter(trailing_slash=False)

router.register('banner', DashboardBannerViewSet)
router.register('faq', FAQDataViewSet)
router.register('flyers',FlyerSchedulerViewSet)
router.register('flyer_image',FlyerImagesViewSet)

urlpatterns = [
    path('details', DashboardAPIView.as_view()),
    path('homecare_details', HomeCareDashboardAPIView.as_view()),
    path('ios_version_check',IOSVersionCheck.as_view()),
    path('remove_account', RemoveAccountAPIView.as_view()),
    path('remove_uhid', RemoveUHIDAPIView.as_view()),
    path('faq_data', FAQDataAPIView.as_view()),
    *router.urls
]