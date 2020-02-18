from django.conf.urls import url
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (DoctorsView, HealthPackagesView, ItemsTarrifPriceView,
                    LabRadiologyItemsView, DepartmentsView,
                    ValidateOTPView, ValidateUHIDView)

router = DefaultRouter(trailing_slash=False)


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
