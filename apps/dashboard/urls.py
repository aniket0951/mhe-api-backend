from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import DashboardBannerViewSet, DashboardAPIView

app_name = 'dashboard'

router = DefaultRouter(trailing_slash=False)

router.register('banner', DashboardBannerViewSet)

urlpatterns = [
    path('', DashboardAPIView.as_view()),

    *router.urls
]