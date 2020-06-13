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

    started_at = models.DateTimeField(blank=True, null=True)

    completed_at = models.DateTimeField(blank=True, null=True)

    recording_link = models.URLField(max_length=500,
                                     null=True,
                                     blank=True,
                                     )
