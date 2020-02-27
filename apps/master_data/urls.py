from django.conf.urls import url
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (DepartmentsView, DepartmentViewSet, DoctorsView,
                    HealthPackagesView, HospitalViewSet, ItemsTarrifPriceView,
                    LabRadiologyItemsView, SpecialisationViewSet,
                    ValidateOTPView, ValidateUHIDView)

router = DefaultRouter(trailing_slash=False)

router.register('all_hospitals', HospitalViewSet)
router.register('all_departments', DepartmentViewSet)
router.register('all_specialisations', SpecialisationViewSet)


urlpatterns = [

    url('^departments', DepartmentsView.as_view(),
        name="departments"),

    url('^doctors', DoctorsView.as_view(),
        name="doctors"),

    url('^health_packages', HealthPackagesView.as_view(),
        name="health_packages"),

    url('^lab_and_radiology_items', LabRadiologyItemsView.as_view(),
        name="lab_and_radiology"),

    url('^items_tariff_price', ItemsTarrifPriceView.as_view(),
        name="lab_and_radiology"),

    url('^validate_uhid', ValidateUHIDView.as_view(),
        name="validate_uhid"),

    url('^validate_otp', ValidateOTPView.as_view(),
        name="validate_otp"),

    *router.urls
]
