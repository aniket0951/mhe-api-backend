from apps.additional_features.utils import AdditionalFeaturesUtil
from datetime import date, datetime
import json
import ast

from proxy.custom_views import ProxyView
import logging
from utils.utils import manipal_admin_object, patient_user_object
from .serializers import DriveSerializer, StaticInstructionsSerializer
from .models import Drive, StaticInstructions
from utils import custom_viewsets
from utils.custom_permissions import BlacklistDestroyMethodPermission, BlacklistUpdateMethodPermission, IsPatientUser, IsManipalAdminUser
from django_filters.rest_framework import DjangoFilterBackend

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
            AdditionalFeaturesUtil.validate_drive_code(code)

        return qs
    
    def perform_create(self, serializer):
        request_data = self.request.data

        AdditionalFeaturesUtil.datetime_validation_on_creation(request_data)
        
        serializer.validated_data['code'] = AdditionalFeaturesUtil.generate_unique_drive_code(serializer.validated_data['description'])

        serializer_id = serializer.save(is_active=True)

        AdditionalFeaturesUtil.create_drive_inventory(serializer_id.id,request_data)
        
        
    def perform_update(self, serializer):
        request_data = self.request.data
        AdditionalFeaturesUtil.datetime_validation_on_creation(request_data)
        serializer_id = serializer.save()
        AdditionalFeaturesUtil.update_drive_inventory(serializer_id.id,request_data)
        
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
                                    
