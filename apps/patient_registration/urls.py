from django.conf.urls import url
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (CityViewSet, CountryViewSet, LanguageViewSet,
                    ProvinceViewSet, RegionViewSet, RegistrationAPIView,
                    UHIDRegistrationView, ZipcodeViewSet)

router = DefaultRouter(trailing_slash=False)

router.register('countries', CountryViewSet)
router.register('regions', RegionViewSet)
router.register('provinces', ProvinceViewSet)
router.register('cities', CityViewSet)
router.register('zipcodes', ZipcodeViewSet)
router.register('languages', LanguageViewSet)

urlpatterns = [
    path('form_details', RegistrationAPIView.as_view()),
    path('uhid_registration', UHIDRegistrationView.as_view()),

    *router.urls

]
