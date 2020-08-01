from django.shortcuts import render

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, serializers, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from utils import custom_viewsets
from .tasks import send_push_notification
from datetime import datetime, timedelta
from apps.appointments.models import Appointment, HealthPackageAppointment


from utils.custom_permissions import (IsManipalAdminUser, IsPatientUser,
                                      IsSelfUserOrFamilyMember, SelfUserAccess)

from .models import MobileDevice, MobileNotification
from .serializers import MobileDeviceSerializer, MobileNotificationSerializer


class NotificationlistView(custom_viewsets.ReadOnlyModelViewSet):
    queryset = MobileNotification.objects.all()
    serializer_class = MobileNotificationSerializer
    permission_classes = [IsPatientUser]
    create_success_message = None
    list_success_message = 'Notification list returned successfully!'
    retrieve_success_message = 'Notification information returned successfully!'
    update_success_message = None

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(recipient_id=self.request.user.id)


class MobileDeviceViewSet(APIView):
    permission_classes = (IsPatientUser,)
    queryset = MobileDevice.objects.all()

    def post(self, request, format=None):
        if not (request.data["token"] and request.data["platform"]):
            raise ValidationError(
                "Token or Platform is missing!")
        device = MobileDevice.objects.filter(
            participant_id=self.request.user.id).first()
        serializer = MobileDeviceSerializer(data=request.data)
        if device:
            serializer = MobileDeviceSerializer(
                device, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_200_OK)
                
    