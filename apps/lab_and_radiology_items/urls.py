from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (HomeCareServiceViewSet, HomeCollectionAppointmentViewSet,
                    HomeCollectionViewSet, PatientServiceAppointmentViewSet)

app_name = 'home_care'

router = DefaultRouter(trailing_slash=False)

router.register('home_collection', HomeCollectionViewSet)
router.register('services', HomeCareServiceViewSet)
router.register('service_appointments', PatientServiceAppointmentViewSet)
router.register('home_collection_appointments',HomeCollectionAppointmentViewSet)

urlpatterns = [
    *router.urls
]
