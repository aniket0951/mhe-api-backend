from apps.master_data.serializers import MedicineSerializer
from apps.doctors.serializers import HospitalSerializer
import logging

from utils.utils import generate_pre_signed_url, manipal_admin_object, patient_user_object
from utils.serializers import DynamicFieldsModelSerializer
from .models import Drive, DriveBilling, DriveBooking, DriveInventory, StaticInstructions
        
logger = logging.getLogger('django')


class DriveSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Drive
        exclude = ('created_at', 'updated_at',)
        
    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        response_object['qr_code'] = None
        try:
            if instance.qr_code:
                response_object['qr_code'] = generate_pre_signed_url(instance.qr_code.url)
            if instance.hospital:
                    response_object['hospital'] = HospitalSerializer(instance.hospital).data

            drive_billing_ids = DriveBilling.objects.filter(drive_id=instance.id)
            response_object['drive_billings'] = DriveBillingSerializer(drive_billing_ids,many=True).data

            admin_object = manipal_admin_object(self.context['request'])
            if admin_object:
                drive_inventory_ids = DriveInventory.objects.filter(drive_id=instance.id)
                response_object['drive_inventories'] = DriveInventorySerializer(drive_inventory_ids,many=True).data

            if patient_user_object(self.context['request']):
                drive_inventory_ids = DriveInventory.objects.filter(drive_id=instance.id)
                drive_inventories_list = DriveInventorySerializer(drive_inventory_ids,many=True).data
            
                drive_inventories_combined = {}
                for drive_inventory in  drive_inventories_list:
                    if drive_inventory.get("medicine").get("id") not in drive_inventories_combined:
                        medicine_obj = drive_inventory.get("medicine")
                        medicine_obj.pop("additional_details")
                        drive_inventories_combined[drive_inventory.get("medicine").get("id")] = {
                            "medicine":medicine_obj,
                            "drive":drive_inventory.get("drive"),
                            "inventory":[]
                        }
                    drive_inventories_combined[drive_inventory.get("medicine").get("id")]["inventory"].append({
                        "id":drive_inventory.get("id"),
                        "dose":drive_inventory.get("dose"),
                        "mh_item_code": drive_inventory.get("mh_item_code"),
                        "item_quantity": drive_inventory.get("item_quantity"),
                        "price": drive_inventory.get("price")
                    })

                response_object['drive_inventories'] = [drive_inventories_combined[key] for key in drive_inventories_combined]

        except Exception as error:
            logger.info("Exception in DriveSerializer -> to_representation: %s"%(str(error)))
            
        return response_object

class DriveInventorySerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = DriveInventory
        exclude = ('created_at', 'updated_at',)

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        try:
            response_object['medicine'] = None
            if instance.medicine:
                response_object['medicine'] = MedicineSerializer(instance.medicine).data
        except Exception as error:
            logger.info("Exception in DriveInventorySerializer: %s"%(str(error)))
        return response_object
            
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