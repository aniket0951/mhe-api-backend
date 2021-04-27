from apps.video_conferences.constants import VideoConferencesConstants
import base64
import json
import hashlib
import logging
import xml.etree.ElementTree as ET

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
from proxy.custom_serializables import \
    SendVcStatus as serializable_SendVcStatus
from proxy.custom_serializers import ObjectSerializer as custom_serializer
from proxy.custom_views import ProxyView
from rest_framework import filters, generics, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView
from rest_framework_jwt.utils import jwt_encode_handler, jwt_payload_handler
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import ChatGrant, SyncGrant, VideoGrant
from twilio.rest import Client
from utils import custom_viewsets
from utils.custom_permissions import (InternalAPICall, IsDoctor,
                                      IsManipalAdminUser, IsPatientUser,
                                      IsSelfUserOrFamilyMember, SelfUserAccess)

from .models import VideoConference
from .serializers import VideoConferenceSerializer
from .utils import create_room_parameters
from utils.custom_jwt_whitelisted_tokens import WhiteListedJWTTokenUtil

client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_ACCOUNT_AUTH_KEY)
logger = logging.getLogger('django')

class RoomCreationView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
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
        data = dict()
        if not appointment:
            raise ValidationError("Appointment does not Exist")
        notification_data = {}
        notification_data["title"] = "Doctor is available for Video consultancy"
        user_message = "Please join the meeting. Doctor is ready for consultation"
        notification_data["notification_type"] = "VIDEO_CONSULTATION"
        notification_data["appointment_id"] = appointment.appointment_identifier
        notification_data["doctor_name"] = appointment.doctor.name
        notification_data["message"] = user_message
        if VideoConference.objects.filter(room_name=room_name).exists():
            if appointment.vc_appointment_status == 5:
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
                send_push_notification.delay(
                    notification_data=notification_data)
                appointment.enable_join_button = True
                appointment.vc_appointment_status = 2
                appointment.save()
            return Response({
                        "message": VideoConferencesConstants.ROOM_ALREADY_EXISTS
                    }, status=status.HTTP_200_OK)
        room = None
        channel = None
        try:
            room = client.video.rooms.create(
                                record_participants_on_connect=True, 
                                type='group', 
                                unique_name=room_name
                            )
            channel = client.chat.services(
                                settings.TWILIO_CHAT_SERVICE_ID
                            ).channels.create(
                                unique_name=room_name
                            )
        except Exception as error:
            logger.error("Exception in RoomCreationView %s"%(str(error)))
        data["appointment"] = appointment.id
        data["room_name"] = room.unique_name
        data["room_sid"] = room.sid
        data["channel_sid"] = channel.sid
        data["recording_link"] = room.links["recordings"]
        video_instance = VideoConferenceSerializer(data=data)
        video_instance.is_valid(raise_exception=True)
        video_instance.save()
        if appointment.family_member:
            member = FamilyMember.objects.filter(
                                    id = appointment.family_member.id, 
                                    patient_info_id=appointment.patient.id
                                ).first()
            if Patient.objects.filter(uhid_number__isnull=False, uhid_number=member.uhid_number).exists():
                patient_member = Patient.objects.filter(uhid_number=member.uhid_number).first()
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
        room_instance = VideoConference.objects.filter(
            room_name=room_name).first()
        if not room_instance:
            raise ValidationError(VideoConferencesConstants.ROOM_DOES_NOT_EXIST)
        channel_sid = room_instance.channel_sid
        try:
            client.chat.services(settings.TWILIO_CHAT_SERVICE_ID).channels(channel_sid).members.create(identity=identity)
        except Exception as error:
            logger.error("Exception in AccessTokenGenerationView %s"%(str(error)))
        if Patient.objects.filter(id=request.user.id).exists():
            if not appointment.patient_ready:
                param = dict()
                param["app_id"] = appointment.appointment_identifier
                param["location_code"] = appointment.hospital.code
                param["set_status"] = "ARRIVED"
                status_param = create_room_parameters(param)
                SendStatus.as_view()(status_param)
            appointment.patient_ready = True
        if Doctor.objects.filter(id=request.user.id).exists():
            appointment.vc_appointment_status = 3
        appointment.save()
        return Response(data={"token": token.to_jwt(), "channel_sid": channel_sid}, status=status.HTTP_200_OK)


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
            raise ValidationError(VideoConferencesConstants.ROOM_DOES_NOT_EXIST)
        room_sid = room_instance.room_sid
        channel_sid = room_instance.channel_sid
        room_status = client.video.rooms(room_sid).fetch().status
        if room_status == "in-progress":
            client.video.rooms(room_sid).update(status="completed")
        notification_data = {
            "patient": PatientSerializer(appointment.patient).data,
            "appointment_id": appointment.appointment_identifier
        }
        param = dict()
        param["app_id"] = appointment.appointment_identifier
        param["location_code"] = appointment.hospital.code
        param["set_status"] = "DEPARTED"
        status_param = create_room_parameters(param)
        SendStatus.as_view()(status_param)
        send_silent_push_notification.delay(
            notification_data=notification_data)
        client.chat.services(settings.TWILIO_CHAT_SERVICE_ID).channels(channel_sid).delete()
        return Response(status=status.HTTP_200_OK)


class InitiateTrackerAppointment(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        doctor_code = request.data.get("doctor_code")
        appointment_identifier = request.data.get("appointment_identifier")
        encoded_string = request.data.get("checksum")
        if not (encoded_string and doctor_code and appointment_identifier):
            raise ValidationError("Invalid Parameter")
        secret_key = settings.SMS_SECRET_KEY
        checksum_string = appointment_identifier + secret_key + doctor_code
        encoded_string_generated = base64.b64encode(hashlib.sha256(checksum_string.encode()).hexdigest().encode()).decode()
        if not (encoded_string == encoded_string_generated):
            raise ValidationError("Invalid Parameter")
        doctor = Doctor.objects.filter(code=doctor_code).exclude(hospital_departments=None).first()

        payload = jwt_payload_handler(doctor)
        payload["username"] = doctor.code
        token = jwt_encode_handler(payload)

        WhiteListedJWTTokenUtil.create_token(doctor,token)

        redirect_data = dict()
        redirect_data["token"] = token
        redirect_data["appointment_identifier"] = appointment_identifier
        redirect_data_string = json.dumps(redirect_data)
        encoded_string = base64.b64encode(redirect_data_string.encode("utf-8"))

        param = str(encoded_string)[2:-1]
        result = settings.VC_URL_REDIRECTION + param
        param = create_room_parameters({"appointment_id": appointment_identifier})
        response = RoomCreationView.as_view()(param)
        message = "Something went wrong"
        if response.status_code == 200:
            if response.data.get("room_name"):
                message = "Room Created"
            elif response.data.get("message") == VideoConferencesConstants.ROOM_ALREADY_EXISTS:
                message = VideoConferencesConstants.ROOM_ALREADY_EXISTS
            return Response({"message": message, "url": result}, status=status.HTTP_200_OK)
        elif response.status_code == 417:
            return Response({
                        "Message": "Video Consultation is Open", 
                        "uhid": response.data["appointment"][0]["uhid"],
                        "appointment_date": response.data["appointment"][0]["appointment_date"], 
                        "appointment_time": response.data["appointment"][0]["appointment_slot"]
                    }, 
                    status=status.HTTP_200_OK)
        return Response({
                    "Error": "Something Went Wrong"
                }, status=status.HTTP_404_NOT_FOUND)


class SendStatus(ProxyView):
    permission_classes = [AllowAny]
    source = 'setVCStatus'

    def get_request_data(self, request):
        vc_status = serializable_SendVcStatus(**request.data)
        request_data = custom_serializer().serialize(vc_status, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        message = "Not Updated"
        status = "Failed"
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            status = root.find("Status").text
            message = root.find("Message").text
            if status == "1":
                status = "success"
        return self.custom_success_response(message=message, success=status)


class HoldAppointmentView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        room_name = request.data.get("room_name", None)
        appointment = Appointment.objects.filter(
            appointment_identifier=room_name).first()
        if appointment:
            appointment.vc_appointment_status, appointment.enable_join_button, appointment.patient_ready = 5, False, False
            appointment.save()
        room_name = "".join(room_name.split("||"))
        room_instance = VideoConference.objects.filter(
            room_name=room_name).first()
        if not room_instance:
            raise ValidationError(VideoConferencesConstants.ROOM_DOES_NOT_EXIST)
        room_sid = room_instance.room_sid
        room_status = client.video.rooms(room_sid).fetch().status
        if room_status == "in-progress":
            client.video.rooms(room_sid).update(status="completed")
        param = dict()
        param["app_id"] = appointment.appointment_identifier
        param["location_code"] = appointment.hospital.code
        param["set_status"] = "DEPARTED"
        status_param = create_room_parameters(param)
        SendStatus.as_view()(status_param)

        notification_data = {}
        notification_data["title"] = "Consultation On Hold"
        notification_data["message"] = "Doctor has put the consultation on Hold"
        notification_data["notification_type"] = "HOLD_VC_NOTIFICATION"
        notification_data["appointment_id"] = appointment.appointment_identifier
        notification_data["doctor_name"] = appointment.doctor.name

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

        return Response(status=status.HTTP_200_OK)
