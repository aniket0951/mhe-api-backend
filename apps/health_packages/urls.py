from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (HealthPackageSlotAvailability,
                    HealthPackageSpecialisationViewSet, HealthPackageViewSet, HealthPackagePrice)

app_name = 'health_package'

router = DefaultRouter(trailing_slash=False)

router.register('specialisation', HealthPackageSpecialisationViewSet)
router.register('', HealthPackageViewSet)


urlpatterns = [
    path('health_package_slot', HealthPackageSlotAvailability.as_view()),
    path('health_package_price', HealthPackagePrice.as_view()),
    
    *router.urls
]
