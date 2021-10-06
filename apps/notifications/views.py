import logging
from datetime import datetime
from rest_framework import  status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.notifications.utils import create_notification_template, read_excel_file_data
from utils import custom_viewsets
from apps.patients.models import Patient
from utils.custom_permissions import (IsManipalAdminUser, IsPatientUser)
from rest_framework.serializers import ValidationError
from .models import MobileDevice, MobileNotification, NotificationTemplate, ScheduleNotifications
from .serializers import MobileDeviceSerializer, MobileNotificationSerializer, NotificationTemplateSerializer, ScheduleNotificationsSerializer
from .tasks import send_push_notification, trigger_scheduled_notification
from django.conf import settings
from rest_framework.parsers import MultiPartParser

logger = logging.getLogger("django")

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


class ManagePushNotificationsViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsManipalAdminUser]
    model = MobileNotification
    queryset = MobileNotification.objects.all()
    serializer_class = MobileNotificationSerializer
    create_success_message = "Notification added successfully!"
    list_success_message = 'Notifications returned successfully!'
    retrieve_success_message = 'Notification returned successfully!'
    update_success_message = 'Notification updated successfully!'
    delete_success_message = 'Notification deleted successfully!'
   
class PushNotificationViewSet(APIView):
    permission_classes = (AllowAny,)
    queryset = MobileNotification.objects.all()
    serializer_class = MobileNotificationSerializer

    def post(self, request, format=None):
        user_id_list = self.request.data.get("user_id_list")
        selected_all = self.request.data.get("selected_all", False)
        notification_data = dict()
        notification_data["title"] = self.request.data.get("title")
        notification_data["message"] = self.request.data.get("user_message")
        notification_data["notification_type"] = "GENERAL_NOTIFICATION"
        notification_data["appointment_id"] = None
        notification_data["notification_image_url"] = self.request.data.get("notification_image_url")

        if selected_all:
            device_qs = MobileDevice.objects.all()
            for each_device in device_qs:
                patient_id = each_device.participant.id
                notification_data["recipient"] = patient_id
                send_push_notification.delay(notification_data=notification_data)

            return Response(status=status.HTTP_200_OK)

        if not user_id_list:
            raise ValidationError("Parameter Missing")

        user_list = user_id_list.split(",")
        for user in user_list:
            patient = Patient.objects.filter(id=user).first()
            if patient:
                notification_data["recipient"] = patient.id
                send_push_notification.delay(notification_data=notification_data)
                
        return Response(status=status.HTTP_200_OK)

class NotificationTemplateViewSet(custom_viewsets.CreateUpdateListRetrieveModelViewSet):
    permission_classes = [IsManipalAdminUser]
    model = NotificationTemplate
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    create_success_message = "Notification template added successfully!"
    list_success_message = 'Notifications templated returned successfully!'
    
class ScheduleNotificationViewSet(custom_viewsets.ListCreateViewSet):
    permission_classes = [IsManipalAdminUser]
    parser_classes = [MultiPartParser]
    model = ScheduleNotifications
    queryset = ScheduleNotifications.objects.all()
    serializer_class = ScheduleNotificationsSerializer
    create_success_message = "Notification send successfully!"
    list_success_message = 'Notifications returned successfully!'
    
    def create(self, request):

        request_data = dict(request.data)
        
        notification_subject    = request_data.get("notification_subject", None)
        notification_body       = request_data.get("notification_body", None)
        template_id             = request_data.get("template_id", None)
        
        if not template_id and not notification_subject and not notification_body:
            raise ValidationError("Kindly provide either template or notification subject & body.")

        excel_file = request.FILES.get("file")
        if not excel_file and not request_data.get('uhids',None):
            raise ValidationError("Kindly provide either List of UHIDs or Excel file")

        if not template_id:
            request_data['template_id'] = create_notification_template(notification_subject,notification_body)

        if excel_file:
            request_data['uhids']  = read_excel_file_data(excel_file)
        
        if request_data["trigger_type"] == ScheduleNotifications.TRIGGER_CHOICE_NOW:
            request_data['date'] = datetime.now().date()
            request_data['time'] = datetime.now().time()
    
        serializer = self.serializer_class(data=request_data)
        serializer.is_valid(raise_exception=True)
        scheduler = serializer.save()

        if scheduler.trigger_type == ScheduleNotifications.TRIGGER_CHOICE_NOW:
            trigger_scheduled_notification(scheduler)

        data = {
            "data" : serializer.data,
            "message"  : "Notification scheduled successfully!"
        }
        return Response(data=data, status=status.HTTP_200_OK)
