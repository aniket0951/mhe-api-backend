
from django.urls import path

from rest_framework import routers
from rest_framework.routers import DefaultRouter

from .views import (AccessTokenGenerationView, CloseRoomView,
                    HoldAppointmentView, InitiateTrackerAppointment,
                    RoomCreationView, SendStatus)

router = DefaultRouter(trailing_slash=False)


urlpatterns = [
    path('room_creation', RoomCreationView.as_view()),
    path('access_token_generation', AccessTokenGenerationView.as_view()),
    path('initiate_vc', InitiateTrackerAppointment.as_view()),
    path('close_room', CloseRoomView.as_view()),
    path('send_status', SendStatus.as_view()),
    path('hold_appointment', HoldAppointmentView.as_view()),
    *router.urls

]
