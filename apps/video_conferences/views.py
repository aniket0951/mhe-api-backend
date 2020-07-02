import requests
from django.conf import settings
from django.db.models import Q

import rest_framework
from apps.appointments.models import Appointment
from apps.appointments.serializers import AppointmentSerializer
from apps.doctors.models import Doctor
from apps.notifications.tasks import (send_push_notification,
                                      send_silent_push_notification)
from apps.patients.models import FamilyMember, Patient
from apps.patients.serializers import FamilyMemberSerializer, PatientSerializer
from rest_framework import filters, generics, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import ChatGrant, SyncGrant, VideoGrant
from twilio.rest import Client
from utils import custom_viewsets
from utils.custom_permissions import (InternalAPICall, IsDoctor,
                                      IsManipalAdminUser, IsPatientUser,
                                      IsSelfUserOrFamilyMember, SelfUserAccess)

from .models import VideoConference
from .serializers import VideoConferenceSerializer


class RoomCreationView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        client = Client(settings.TWILIO_ACCOUNT_SID,
                        settings.TWILIO_ACCOUNT_AUTH_KEY)
        appointment_id = request.data.get("appointment_id")
        appointment = Appointment.objects.filter(
            appointment_identifier=appointment_id).first()
        doctor = appointment.doctor
        doctor_appointments = Appointment.objects.filter(Q(doctor=doctor.id) & Q(appointment_mode="VC") & Q(
            payment_status="success") & Q(status=1) & (Q(vc_appointment_status=2) | Q(vc_appointment_status=3)))
        if doctor_appointments:
            serializer = AppointmentSerializer(doctor_appointments, many=True)
            data = {
                "appointment": serializer.data,
                "message": "Please complete the initiated meeting Before starting new one"
            }
            return Response(data=data, status=status.HTTP_417_EXPECTATION_FAILED)
        room_name = "".join(appointment_id.split("||"))
        if not appointment:
            raise ValidationError("Appointment does not Exist")
        room = client.video.rooms.create(
            record_participants_on_connect=True,
            type='group',
            unique_name=room_name
        )
        channel = client.chat.services(
            settings.TWILIO_CHAT_SERVICE_ID).channels.create(unique_name=room_name)
        data = dict()
        data["appointment"] = appointment.id
        data["room_name"] = room.unique_name
        data["room_sid"] = room.sid
        data["channel_sid"] = channel.sid
        data["recording_link"] = room.links["recordings"]
        video_instance = VideoConferenceSerializer(data=data)
        video_instance.is_valid(raise_exception=True)
        video_instance.save()
        notification_data = {}
        notification_data["title"] = "Doctor is available for Video consultancy"
        user_message = "Plese Join the meeting. Doctor is ready for consultation"
        notification_data["notification_type"] = "VIDEO_CONSULTATION"
        notification_data["appointment_id"] = appointment.appointment_identifier
        notification_data["message"] = user_message
        if appointment.family_member:
            member = FamilyMember.objects.filter(
                id=appointment.family_member.id, patient_info_id=appointment.patient.id).first()
            if Patient.objects.filter(uhid_number__isnull=False, uhid_number=member.uhid_number).exists():
                patient_member = Patient.objects.filter(
                    uhid_number=member.uhid_number).first()
                notification_data["recipient"] = patient_member.id
                send_push_notification.delay(
                    notification_data=notification_data)
        notification_data["recipient"] = appointment.patient.id
        send_push_notification.delay(notification_data=notification_data)
        data["vc_appointment_status"] = 2
        appointment.enable_join_button = True
        appointment.vc_appointment_status = 2
        appointment.save()
        return Response(data=data, status=status.HTTP_200_OK)


class AccessTokenGenerationView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        room = request.data.get("room")
        room_name = "".join(room.split("||"))
        identity = request.data.get("identity")
        appointment = Appointment.objects.filter(
            appointment_identifier=room).first()
        if not appointment:
            raise ValidationError("Invalid room name")
        if appointment.vc_appointment_status == 4:
            raise ValidationError("Meeting Room is closed")
        token = AccessToken(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_API_KEY_SID,
                            settings.TWILIO_API_KEY_SECRET, identity=identity)
        chat_grant = ChatGrant(service_sid=settings.TWILIO_CHAT_SERVICE_ID)
        token.add_grant(chat_grant)
        video_grant = VideoGrant(room=room_name)
        token.add_grant(video_grant)
        if Patient.objects.filter(id=request.user.id).exists():
            appointment.patient_ready = True
        if Doctor.objects.filter(id=request.user.id).exists():
            appointment.vc_appointment_status = 3
        appointment.save()
        return Response(data={"token": token.to_jwt()}, status=status.HTTP_200_OK)


class CloseRoomView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        room_name = request.data.get("room_name", None)
        appointment = Appointment.objects.filter(
            appointment_identifier=room_name).first()
        if appointment:
            appointment.vc_appointment_status, appointment.enable_join_button, appointment.patient_ready = 4, False, False
            appointment.save()
        room_name = "".join(room_name.split("||"))
        room_instance = VideoConference.objects.filter(
            room_name=room_name).first()
        if not room_instance:
            raise ValidationError("Room does not Exist")
        room_sid = room_instance.room_sid
        client = Client(settings.TWILIO_ACCOUNT_SID,
                        settings.TWILIO_ACCOUNT_AUTH_KEY)
        room_status = client.video.rooms(room_sid).fetch().status
        if room_status == "in-progress":
            room = client.video.rooms(room_sid).update(status="completed")
        notification_data = {
            "patient": PatientSerializer(appointment.patient).data,
            "appointment_id": appointment.appointment_identifier
        }
        send_silent_push_notification.delay(
            notification_data=notification_data)
        return Response(status=status.HTTP_200_OK)


class ChatAccessTokenGenerationView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        room = request.data.get("room")
        room_name = "".join(room.split("||"))
        identity = request.data.get("identity")
        appointment = Appointment.objects.filter(
            appointment_identifier=room).first()
        if not appointment:
            raise ValidationError("Invalid room name")
        token = AccessToken(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_API_KEY_SID,
                            settings.TWILIO_API_KEY_SECRET, identity=identity)
        chat_grant = ChatGrant(service_sid=settings.TWILIO_CHAT_SERVICE_ID)
        token.add_grant(chat_grant)
        return Response(data={"token": token.to_jwt()}, status=status.HTTP_200_OK)
