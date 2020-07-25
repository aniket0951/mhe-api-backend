from django.conf.urls import url
from django.urls import path

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter(trailing_slash=False)

router.register('details', views.DoctorsAPIView)

urlpatterns = [
    path('login', views.DoctorloginView.as_view()),
    path('reschedule_slot', views.DoctorRescheduleSlot.as_view()),
    path('slot', views.DoctorSlotAvailability.as_view()),
    path('schedule', views.DoctorScheduleView.as_view()),
    path('next_slot', views.NextSlotAvailable.as_view()),
    *router.urls

]
