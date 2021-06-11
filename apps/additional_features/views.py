from datetime import date, datetime
from utils.utils import start_end_datetime_comparision
from .serializers import DriveSerializer, StaticInstructionsSerializer
from .models import Drive, StaticInstructions
from utils import custom_viewsets
from utils.custom_permissions import BlacklistDestroyMethodPermission, BlacklistUpdateMethodPermission, IsPatientUser, IsManipalAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.serializers import ValidationError
from rest_framework import filters


class StaticInstructionsViewSet(custom_viewsets.ReadOnlyModelViewSet):
    queryset = StaticInstructions.objects.all()
    serializer_class = StaticInstructionsSerializer
    permission_classes = [IsPatientUser]
    list_success_message = 'Static Instructions returned successfully!'
    retrieve_success_message = 'Static Instruction returned successfully!'
    filter_backends = (
                DjangoFilterBackend,
                filters.SearchFilter, 
                filters.OrderingFilter
            )
    filter_fields = ['instruction_type']
    
class DriveScheduleViewSet(custom_viewsets.ModelViewSet):
    queryset = Drive.objects.all()
    serializer_class = DriveSerializer
    permission_classes = [IsManipalAdminUser | IsPatientUser]
    create_success_message = 'Drive Schedule created successfully!'
    list_success_message = 'Drive Schedules returned successfully!'
    retrieve_success_message = 'Drive Schedule information returned successfully!'
    update_success_message = 'Drive Schedules updated successfully!'

    filter_backends = (
                DjangoFilterBackend,
                filters.SearchFilter, 
                filters.OrderingFilter
            )
    filter_fields = ['type','booking_start_time','code']
    search_fields = ['description','code']
    
    def get_permissions(self):

        if self.action in ['create','partial_update']:
            permission_classes = [IsManipalAdminUser]
            return [permission() for permission in permission_classes]

        if self.action in ['list', 'retrieve']:
            permission_classes = [IsPatientUser | IsManipalAdminUser]
            return [permission() for permission in permission_classes]
        
        if self.action == 'update':
            permission_classes = [BlacklistUpdateMethodPermission]
            return [permission() for permission in permission_classes]

        if self.action == 'destroy':
            permission_classes = [BlacklistDestroyMethodPermission]
            return [permission() for permission in permission_classes]

        return super().get_permissions()
    
    def perform_create(self, serializer):
        current_date = date.today()

        booking_start_time = self.request.data.get('booking_start_time')
        booking_end_time = self.request.data.get('booking_end_time')
        
        if 'booking_start_time' in self.request.data:
            start_date_time = datetime.strptime(booking_start_time,'%Y-%m-%dT%H:%M:%S')
            if start_date_time.date() < current_date:
                raise ValidationError('Start date time should not be set as past date.')

            if 'booking_end_time' in self.request.data:
                start_end_datetime_comparision(booking_start_time,booking_end_time)

        serializer.save(is_active=True)    