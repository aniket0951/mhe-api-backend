from apps.additional_features.utils import AdditionalFeatures
from datetime import date, datetime
import json
import ast

from proxy.custom_views import ProxyView
import logging
from utils.utils import end_date_vaccination_date_comparision, manipal_admin_object, patient_user_object, start_end_datetime_comparision
from .serializers import DriveBookingSerializer, DriveInventorySerializer, DriveSerializer, StaticInstructionsSerializer
from .models import Drive, DriveBooking, DriveInventory, StaticInstructions
from utils import custom_viewsets
from utils.custom_permissions import BlacklistDestroyMethodPermission, BlacklistUpdateMethodPermission, IsPatientUser, IsManipalAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny

from rest_framework.serializers import ValidationError
from rest_framework import filters
import xml.etree.ElementTree as ET
from proxy.custom_serializables import \
    DriveItemPrice as serializable_DriveItemPrice
from proxy.custom_serializers import ObjectSerializer as custom_serializer

    
logger = logging.getLogger("additional_features")

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
    
class DriveScheduleViewSet(custom_viewsets.CreateUpdateListRetrieveModelViewSet):
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

    def get_queryset(self):

        qs = super().get_queryset()

        admin_object = manipal_admin_object(self.request)
        if admin_object:
            pass

        code = self.request.query_params.get('code')
        if patient_user_object(self.request):
            drive_id = None
            try:
                drive_id = Drive.objects.get(code=code)
            except Exception as e:
                logger.debug("Exception in get_queryset -> patient_user_object : %s"%(str(e)))
            if not drive_id:
                raise ValidationError("No drive available for the entered code.")
            current_date = datetime.today()
            if drive_id.booking_start_time > current_date:
                raise ValidationError('Bookings for the drive has not been started yet.')
            if drive_id.booking_end_time < current_date:
                raise ValidationError('Bookings for the drive has been closed.')
        return qs
    
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
                date_of_vaccination_date = self.request.data.get('date')
                end_date_vaccination_date_comparision(booking_end_time,date_of_vaccination_date)
            
        serializer.validated_data['code'] = AdditionalFeatures.generate_unique_drive_code(serializer.validated_data['description'])

        serializer.save(is_active=True)   
        
    def perform_update(self, serializer):
        if 'booking_start_time' in self.request.data and 'booking_end_time' in self.request.data:
            
            start_date_time = self.request.data.get('booking_start_time')
            end_date_time = self.request.data.get('booking_end_time')

            start_end_datetime_comparision(start_date_time,end_date_time)
            
        serializer.save()
        
class DriveItemCodePriceView(ProxyView):
    permission_classes = [IsManipalAdminUser]
    source = 'OPItemPrice'

    def get_request_data(self, request):
        item_code_price = serializable_DriveItemPrice(**request.data)
        request_data = custom_serializer().serialize(item_code_price, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)
   
    def parse_proxy_response(self, response):
        root = ET.fromstring(response.content)
        status = root.find("Status").text
        response_message = {}
        message = "Could not fetch the price for the Item Code"
        success = False
        if status == "1":
            item_price_details = root.find("OPItemPriceDetails").text
            if item_price_details:
                item_price_details_json = ast.literal_eval(item_price_details)
                response_message = item_price_details_json
                message = "success"
                success = True
        return self.custom_success_response(
                                        message=message,
                                        success=success, 
                                        data=response_message
                                    )
        
    def perform_update(self, serializer):
        serializer.save() 
        
class DriveInventoryViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsManipalAdminUser]
    model = DriveInventory
    queryset = DriveInventory.objects.all()
    serializer_class = DriveInventorySerializer
    create_success_message = 'Drive Inventory added successfully!'
    list_success_message = 'Drive Inventories returned successfully!'
    retrieve_success_message = 'Drive Inventory returned successfully!'
    update_success_message = 'Drive Inventory updated successfully!'
    delete_success_message = 'Drive Inventory deleted successfully!'
    
class DriveBookingViewSet(custom_viewsets.ModelViewSet):
    permission_classes = [IsManipalAdminUser | IsPatientUser]
    model = DriveBooking
    queryset = DriveBooking.objects.all()
    serializer_class = DriveBookingSerializer
    create_success_message = 'Drive booked successfully!'
    list_success_message = 'Drive Bookings returned successfully!'
    retrieve_success_message = 'Drive Booking returned successfully!'
    update_success_message = 'Drive Booking updated successfully!'
    delete_success_message = 'Drive Booking deleted successfully!'
    
    filter_backends = (
                DjangoFilterBackend,
                filters.SearchFilter, 
                filters.OrderingFilter
            )
    filter_fields = ['status']
    
    def get_permissions(self):

        if self.action in ['create','partial_update']:
            permission_classes = [IsPatientUser]
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
        drive = self.request.data.get('drive')
        drive_inventory = self.request.data.get('drive_inventory')
        status = self.request.data.get('status')
       
        drive_inventories_count = DriveBooking.objects.filter(drive_inventory=drive_inventory,drive=drive,status=status).exclude(status="cancelled").count()
        
        item_quantity  = DriveInventory.objects.filter(id=drive_inventory).values_list('item_quantity',flat=True)[0]
        
        if drive_inventories_count > item_quantity:
            raise ValidationError("Sorry! All vaccines are consumed for the selected vaccine, You can book with another Vaccine")
        
        serializer.save()
                                    
