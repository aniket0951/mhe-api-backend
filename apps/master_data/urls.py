from django.conf.urls import url
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ValidateUHIDView, ValidateOTPView, SpecialisationsView

router = DefaultRouter(trailing_slash=False)


urlpatterns = [

    url('^specialisation_details', SpecialisationsView.as_view(),
        name="specialisation_details"),

    url('^validate_uhid', ValidateUHIDView.as_view(),
        name="validate_uhid"),

    url('^validate_otp', ValidateOTPView.as_view(),
        name="validate_otp"),

    *router.urls
]
