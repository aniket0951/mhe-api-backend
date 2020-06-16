from django.urls import include, path

from rest_framework import routers
from rest_framework.routers import DefaultRouter

from .views import (AppointmentsAPIView, CancelAndRefundView,
                    CancelHealthPackageAppointment, CancellationReasonlistView,
                    CancelMyAppointment, CreateMyAppointment,
                    DoctorRescheduleAppointmentView, DoctorsAppointmentAPIView,
                    HealthPackageAppointmentView, OfflineAppointment,
                    RecentlyVisitedDoctorlistView, UpcomingAppointmentsAPIView)

router = DefaultRouter(trailing_slash=False)

router.register('all_appointments', AppointmentsAPIView)
router.register('all_doctors_appointments', DoctorsAppointmentAPIView)
router.register('upcoming_appointments', UpcomingAppointmentsAPIView)
router.register('recently_visited_doctor', RecentlyVisitedDoctorlistView)


urlpatterns = [
    path('cancel_appointment', CancelMyAppointment.as_view()),
    path('Cancel_and_refund', CancelAndRefundView.as_view()),
    path('cancel_health_package_appointment',
         CancelHealthPackageAppointment.as_view()),
    path('create_appointment', CreateMyAppointment.as_view()),
    path('offline_appointment', OfflineAppointment.as_view()),
    path('reschedule_appointment', DoctorRescheduleAppointmentView.as_view()),
    path('create_health_package_appointment',
         HealthPackageAppointmentView.as_view()),
    path('cancellation_reason',
         CancellationReasonlistView.as_view({'get': 'list'})),
    *router.urls

]
