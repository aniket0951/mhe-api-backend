from django.conf.urls import url
from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.phlebo.views import PhleboAPIView

app_name = 'phlebo'

router = DefaultRouter(trailing_slash=False)
router.register('phlebo',PhleboAPIView)

urlpatterns = [
   * router.urls
]
