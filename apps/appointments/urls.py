from django.urls import include, path

from rest_framework import routers
from rest_framework.routers import DefaultRouter

from .views import (AppointmentsAPIView, RecentlyVisitedDoctorlistView, CancelMyAppointment,
                    CreateMyAppointment,HealthPackageAppointmentView,CancellationReasonlistView,
                    OfflineAppointment)

router = DefaultRouter(trailing_slash=False)

router.register('all_appointments', AppointmentsAPIView)
router.register('recently_visited_doctor', RecentlyVisitedDoctorlistView)


urlpatterns = [
    path('cancel_appointment', CancelMyAppointment.as_view()),
    path('create_appointment', CreateMyAppointment.as_view()),
    path('offline_appointment', OfflineAppointment.as_view()),
    path('create_health_package_appointment', HealthPackageAppointmentView.as_view()),
    path('cancellation_reason',CancellationReasonlistView.as_view({'get': 'list'})),
    *router.urls

]
