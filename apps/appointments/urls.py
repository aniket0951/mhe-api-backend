
from django.urls import path, include
from rest_framework import routers
from .views import *

urlpatterns = [
    path('allAppointments/', AppointmentsAPIView.as_view()),
    path('createAppointment/',CreateAppointment, name = "CreateAppointment"),
    path('cancelAppointment/',CancelAppointment, name = "cancelAppointment")
]



