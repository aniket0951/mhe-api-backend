from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import UploadPrescriptionViewSet ,HomeCollectionViewSet, HomeCareServiceViewSet, PatientServiceAppointmentViewSet

app_name = 'home_care'

router = DefaultRouter(trailing_slash=False)

router.register('home_collection', HomeCollectionViewSet)
router.register('services', HomeCareServiceViewSet)
router.register('appointments', PatientServiceAppointmentViewSet)
router.register('prescription', UploadPrescriptionViewSet)



urlpatterns = [
    *router.urls
]
