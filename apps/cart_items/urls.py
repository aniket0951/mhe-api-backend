from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import HealthPackageCartViewSet

app_name = 'cart_items'

router = DefaultRouter(trailing_slash=False)

router.register('health_packages', HealthPackageCartViewSet)


urlpatterns = [
    *router.urls
]
