from django.conf.urls import url
from django.urls import path

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter(trailing_slash=False)

router.register('doctors', views.DoctorsAPIView)

urlpatterns = [
    path('doctor_details', views.DoctorSlotAvailability.as_view()),
    *router.urls

]
