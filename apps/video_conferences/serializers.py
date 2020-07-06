from rest_framework import serializers
from utils.serializers import DynamicFieldsModelSerializer

from .models import VideoConference


class VideoConferenceSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = VideoConference
        fields = '__all__'
