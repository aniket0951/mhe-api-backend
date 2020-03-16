
from django.urls import path

from rest_framework import routers
from rest_framework.routers import DefaultRouter
from .views import *


router = DefaultRouter(trailing_slash=False)





urlpatterns = [
    path('appointment_payment', AppointmentPayment.as_view()),
    path('payment_response', PaymentResponse.as_view()),
    path('health_package_payment', HealthPackagePayment.as_view()),
    path('uhid_payment', UHIDPayment.as_view()),

]

