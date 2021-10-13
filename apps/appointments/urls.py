from django.urls import include, path

from rest_framework import routers
from rest_framework.routers import DefaultRouter
from apps.payments.views import AppointmentPaymentView
from .views import (AppointmentDocumentsViewSet,
                    AppointmentPrescriptionViewSet, AppointmentsAPIView,
                    AppointmentVitalViewSet, CancelAndRefundView,
                    CancelHealthPackageAppointment, CancellationReasonlistView,
                    CancelMyAppointment, CreateMyAppointment,
                    CurrentAppointmentListView, CurrentPatientListView,
                    DoctorRescheduleAppointmentView, DoctorsAppointmentAPIView, FeedbackData,
                    FeedbackViewSet, HealthPackageAppointmentView,
                    ManipalPrescriptionViewSet, OfflineAppointment,
                    PrescriptionDocumentsViewSet,
                    RecentlyVisitedDoctorlistView, UpcomingAppointmentsAPIView, 
                    PrimeBenefitsViewSet)

router = DefaultRouter(trailing_slash=False)

router.register('all_appointments', AppointmentsAPIView)
router.register('all_doctors_appointments', DoctorsAppointmentAPIView)
router.register('upload_documents', AppointmentDocumentsViewSet)
router.register('upcoming_appointments', UpcomingAppointmentsAPIView)
router.register('vitals', AppointmentVitalViewSet)
router.register('prescription', PrescriptionDocumentsViewSet)
router.register('feedback', FeedbackViewSet)
router.register('manipal_prescription', ManipalPrescriptionViewSet)
router.register('recently_visited_doctor', RecentlyVisitedDoctorlistView)
router.register('all_prescription', AppointmentPrescriptionViewSet)
router.register('prime_benefits', PrimeBenefitsViewSet)

urlpatterns = [

     path('cancel_appointment', CancelMyAppointment.as_view()),
     path('Cancel_and_refund', CancelAndRefundView.as_view()),
     path('ip_patients', CurrentPatientListView.as_view()),
     path('current_appointments', CurrentAppointmentListView.as_view()),
     path('cancel_health_package_appointment',
         CancelHealthPackageAppointment.as_view()),
     path('create_appointment', CreateMyAppointment.as_view()),
     path('offline_appointment', OfflineAppointment.as_view()),
     path('feedbacks_data', FeedbackData.as_view()),
     path('reschedule_appointment', DoctorRescheduleAppointmentView.as_view()),
     path('create_health_package_appointment',
         HealthPackageAppointmentView.as_view()),
     path('cancellation_reason',
         CancellationReasonlistView.as_view({'get': 'list'})),
     path('payment_update', AppointmentPaymentView.as_view()),
    
     * router.urls

]
