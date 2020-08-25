
from django.conf.urls import url
from django.urls import path

from rest_framework.routers import DefaultRouter

from .views import DischargeViewSet

router = DefaultRouter(trailing_slash=False)

router.register('all_disharge_summary', DischargeViewSet)

urlpatterns = [
    *router.urls
]
