
from django.urls import path

from rest_framework import routers
from rest_framework.routers import DefaultRouter

from .views import (AppointmentPayment, CorporateUhidRegistration,
                    EpisodeItemView, HealthPackageAPIView,
                    HealthPackagePayment, IPDepositPayment, OPBillPayment,
                    PayBillOpView, PayBillView, PaymentReturn,
                    PaymentsAPIView, ReceiptViewSet, RefundView, UHIDPayment)

from .razorpay_views import (
                        RazorAppointmentPayment,
                        RazorDrivePayment,
                        RazorHealthPackagePayment,
                        RazorUHIDPayment,
                        RazorOPBillPayment,
                        RazorIPDepositPayment,
                        RazorPaymentResponse,
                        RazorRefundView
                    )

router = DefaultRouter(trailing_slash=False)
router.register('all_payments', PaymentsAPIView)
router.register('all_health_package', HealthPackageAPIView)
router.register('payment_receipt', ReceiptViewSet)


urlpatterns = [
    path('appointment_payment', AppointmentPayment.as_view()),
    path('health_package_payment', HealthPackagePayment.as_view()),
    path('uhid_payment', UHIDPayment.as_view()),
    path('op_bill_payment', OPBillPayment.as_view()),
    path('ip_deposit_payment', IPDepositPayment.as_view()),

    path('razor_appointment_payment', RazorAppointmentPayment.as_view()),
    path('razor_health_package_payment', RazorHealthPackagePayment.as_view()),
    path('razor_uhid_payment', RazorUHIDPayment.as_view()),
    path('razor_op_bill_payment', RazorOPBillPayment.as_view()),
    path('razor_ip_deposit_payment', RazorIPDepositPayment.as_view()),
    path('razor_payment_response', RazorPaymentResponse.as_view()),
    path('razor_refund', RazorRefundView.as_view()),
    path('razor_drive_booking_payment', RazorDrivePayment.as_view()),
    path('payment_return', PaymentReturn.as_view()),
    path('ip_bill_details', PayBillView.as_view()),
    path('op_bill_details', PayBillOpView.as_view()),
    path('episode_items_details', EpisodeItemView.as_view()),
    path('refund', RefundView.as_view()),
    path('corporate_uhid_registration', CorporateUhidRegistration.as_view()),
    *router.urls
]
