from apps.doctors.serializers import HospitalSerializer
import logging

from utils.utils import generate_pre_signed_url
from utils.serializers import DynamicFieldsModelSerializer
from .models import Drive, DriveBilling, DriveBooking, DriveInventory, StaticInstructions
        
logger = logging.getLogger('django')


class DriveSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Drive
        exclude = ('created_at', 'updated_at',)
        
    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        try:
            if instance.hospital:
                response_object['hospital'] = HospitalSerializer(instance.hospital).data
            if instance.qr_code:
                response_object['qr_code'] = generate_pre_signed_url(instance.qr_code.url)
        except Exception as error:
            logger.info("Exception in DriveSerializer: %s"%(str(error)))
            response_object['qr_code'] = None
        return response_object

class DriveInventorySerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = DriveInventory
        exclude = ('created_at', 'updated_at',)
        
class DriveBillingSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = DriveBilling
        exclude = ('created_at', 'updated_at',)
        
class DriveBookingSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = DriveBooking
        exclude = ('created_at', 'updated_at',)
        
class StaticInstructionsSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = StaticInstructions
        fields = '__all__'