import requests
from django.conf import settings

import rest_framework
from apps.appointments.models import Appointment
from apps.patients.models import FamilyMember, Patient
from rest_framework import filters, generics, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant
from twilio.rest import Client
from utils import custom_viewsets
from apps.notifications.tasks import send_push_notification

from .models import VideoConference
from .serializers import VideoConferenceSerializer
from utils.custom_permissions import (InternalAPICall, IsManipalAdminUser,
                                      IsPatientUser, IsSelfUserOrFamilyMember,
                                      SelfUserAccess, IsDoctor)


class RoomCreationView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        client = Client(settings.TWILIO_ACCOUNT_SID,
                        settings.TWILIO_ACCOUNT_AUTH_KEY)
        appointment_id = request.data.get("appointment_id")
        appointment = Appointment.objects.filter(
            appointment_identifier=appointment_id).first()
        room_name = "".join(appointment_id.split("||"))
        if not appointment:
            raise ValidationError("Appointment does not Exist")
        room = client.video.rooms.create(
            record_participants_on_connect=True,
            type='group',
            unique_name=room_name
        )
        data = dict()
        data["appointment"] = appointment.id
        data["room_name"] = room.unique_name
        data["room_sid"] = room.sid
        data["recording_link"] = room.links["recordings"]
        video_instance = VideoConferenceSerializer(data=data)
        video_instance.is_valid(raise_exception=True)
        video_instance.save()
        notification_data = {}
        notification_data["title"] = "Doctor is available for Video consultancy"
        user_message = "Reminder: You have an appointment with {0}, {1}, {2}, now at {3}. For assistance, call Appointment Helpline 1800 102 5555.".format(appointment_instance.doctor.name, appointment_instance.department.name, appointment_instance.hospital.address,appointment_instance.appointment_slot)
        notification_data["message"] = user_message
        if appointment.family_member:
            member = FamilyMember.objects.filter(
                id=appointment.family_member.id, patient_info_id=appointment.patient.id).first()
            if Patient.objects.filter(uhid_number__isnull=False, uhid_number=member.uhid_number).exists():
                patient_member = Patient.objects.filter(
                    uhid_number=member.uhid_number).first()
                notification_data["recipient"] = patient_member.id
                send_push_notification.delay(notification_data=notification_data)
        notification_data["recipient"] = appointment.patient.id
        send_push_notification.delay(notification_data=notification_data)
        return Response(data=data, status=status.HTTP_200_OK)


class AccessTokenGenerationView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        room = request.data.get("room")
        room_name = "".join(room.split("||"))
        identity = request.data.get("identity")
        token = AccessToken(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_API_KEY_SID,
                            settings.TWILIO_API_KEY_SECRET, identity=identity)
        video_grant = VideoGrant(room=room_name)
        token.add_grant(video_grant)
        return Response(data={"token": token.to_jwt()}, status=status.HTTP_200_OK)


class CloseRoomView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        room_name = request.data.get("room_name", None)
        room_name = "".join(room_name.split("||"))
        room_instance = VideoConference.objects.filter(
            room_name=room_name).first()
        if not room_instance:
            raise ValidationError("Room does not Exist")
        room_sid = room_instance.room_sid
        client = Client(settings.TWILIO_ACCOUNT_SID,
                        settings.TWILIO_ACCOUNT_AUTH_KEY)
        room = client.video.rooms(room_sid).update(status="completed")
        return Response(status=status.HTTP_200_OK)
