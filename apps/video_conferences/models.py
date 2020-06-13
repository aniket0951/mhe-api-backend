import uuid

from django.db import models

from apps.appointments.models import Appointment
from apps.meta_app.models import MyBaseModel


class VideoConference(MyBaseModel):

    appointment = models.ForeignKey(Appointment,
                                    related_name="appointment_video_conference",
                                    on_delete=models.PROTECT,
                                    blank=False,
                                    null=False)

    room_name = models.CharField(max_length=200,
                                 blank=False,
                                 null=False,
                                 verbose_name='Room Name')

    room_sid = models.CharField(max_length=200,
                                blank=False,
                                null=False,
                                verbose_name='Room SID')


class CloseRoomView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        room_sid = request.data.get("room_name", None)
        client = Client(settings.TWILIO_ACCOUNT_SID,
                        settings.TWILIO_ACCOUNT_AUTH_KEY)
        room = client.video.rooms(room_sid).update(status='completed')
        return Response(status=status.HTTP_200_OK)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    recording_link = models.URLField(max_length=500,
                                     null=True,
                                     blank=True,
                                     )
