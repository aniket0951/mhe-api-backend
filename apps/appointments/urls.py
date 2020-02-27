
from django.urls import include, path

from rest_framework import routers

from .views import *

urlpatterns = [
    path('all_appointments/', AppointmentsAPIView.as_view()),
    path('recently_visited_doctor/', RecentlyVisitedDoctorlistView.as_view()),
    path('cancel_appointment/', CancelMyAppointment.as_view()),
    path('create_appointment/', CreateMyAppointment.as_view()),
    path('show_appointment/', ShowAppointmentView.as_view()),
    path('get_data/', get_data, name="get_data"),

]
