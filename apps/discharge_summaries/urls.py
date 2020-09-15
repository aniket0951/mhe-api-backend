
from django.conf.urls import url
from django.urls import path

from rest_framework.routers import DefaultRouter

from .views import DischargeViewSet, DischargeSummarySyncAPIView

router = DefaultRouter(trailing_slash=False)

router.register('all_disharge_summary', DischargeViewSet)

urlpatterns = [
    url('^discharge_sync', DischargeSummarySyncAPIView.as_view(),
        name="sync_discharge"),
        
    *router.urls
]
