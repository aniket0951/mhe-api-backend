
from django.urls import path

from rest_framework import routers
from rest_framework.routers import DefaultRouter

from .views import (AppointmentPayment, EpisodeItemView, HealthPackageAPIView,
                    HealthPackagePayment, PayBillOpView, PayBillView,
                    PaymentResponse, PaymentReturn, PaymentsAPIView,
                    UHIDPayment,OPBillPayment, IPDepositPayment)

router = DefaultRouter(trailing_slash=False)
router.register('all_payments', PaymentsAPIView)
router.register('all_health_package', HealthPackageAPIView)


urlpatterns = [
    path('appointment_payment', AppointmentPayment.as_view()),
    path('payment_response', PaymentResponse.as_view()),
    path('payment_return', PaymentReturn.as_view()),
    path('health_package_payment', HealthPackagePayment.as_view()),
    path('uhid_payment', UHIDPayment.as_view()),
    path('op_bill_payment', OPBillPayment.as_view()),
    path('ip_deposit_payment', IPDepositPayment.as_view()),
    path('ip_bill_details', PayBillView.as_view()),
    path('op_bill_details', PayBillOpView.as_view()),
    path('episode_items_details', EpisodeItemView.as_view()),
    *router.urls

]
