import logging
from apps.health_packages.models import HealthPackage
from rest_framework.test import APIRequestFactory
from django.conf import settings

logger = logging.getLogger("Django")

def create_room_parameters(param, factory=APIRequestFactory()):
    return factory.post(
        '', param, format='json')

def create_room_and_channel(client,room_name):
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
    return room,channel