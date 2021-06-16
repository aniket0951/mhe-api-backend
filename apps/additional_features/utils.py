from apps.additional_features.serializers import DriveBillingSerializer, DriveInventorySerializer
import logging
import random
import re

from datetime import datetime,date
from utils.utils import end_date_vaccination_date_comparision, start_end_datetime_comparision
from apps.additional_features.models import Drive, DriveBilling, DriveInventory
from rest_framework.serializers import ValidationError


logger = logging.getLogger("AdditionalFeaturesUtil")

class AdditionalFeaturesUtil:

    @staticmethod
    def generate_unique_drive_code(description):
        if not description or len(description)<3:
            raise ValidationError("Drive name is too short!")
        while(True):
            try:
                code = AdditionalFeaturesUtil.generate_code(description)
                Drive.objects.get(code=code)
            except Exception as e:
                logger.debug("Exception generate_unique_drive_code: %s"%(str(e)))
                return code

    @staticmethod
    def generate_code(description):
        description = AdditionalFeaturesUtil.remove_whitespaces(description)
        description = description.upper()
        start_index = random.randint(0,len(description)-2)
        return "%s%s"%(str(description[start_index:start_index+2]),str(random.randint(1000,9999)))

    @staticmethod
    def remove_whitespaces(string):
        pattern = re.compile(r'\s+')
        return re.sub(pattern, '', string)

    @staticmethod
    def validate_drive_code(code):
        if not code:
            raise ValidationError("Provide a valid drive code!")
        drive_id = None
        try:
            drive_id = Drive.objects.get(code=code,is_active=True)
        except Exception as e:
            logger.debug("Exception in get_queryset -> patient_user_object : %s"%(str(e)))
        if not drive_id:
            raise ValidationError("No drive available for the entered code.")
        current_date = datetime.today()
        if drive_id.booking_start_time > current_date:
            raise ValidationError('Bookings for the drive has not been started yet.')
        if drive_id.booking_end_time < current_date:
            raise ValidationError('Bookings for the drive has been closed.')

    @staticmethod
    def datetime_validation_on_creation(request_data):
        current_date = date.today()
        booking_start_time = request_data.get('booking_start_time')
        booking_end_time = request_data.get('booking_end_time')
        
        if 'booking_start_time' in request_data:
            
            start_date_time = datetime.strptime(booking_start_time,'%Y-%m-%dT%H:%M:%S')
            if start_date_time.date() < current_date:
                raise ValidationError('Start date time should not be set as past date.')

            if 'booking_end_time' in request_data:
                start_end_datetime_comparision(booking_start_time,booking_end_time)
                date_of_vaccination_date = request_data.get('date')
                end_date_vaccination_date_comparision(booking_end_time,date_of_vaccination_date)

    @staticmethod
    def create_drive_inventory(drive_id,request_data):
        if request_data.get('drive_inventories'):
            for drive_inventory in request_data['drive_inventories']:
                drive_inventory.update({"drive":drive_id})
                drive_inventory_obj = DriveInventorySerializer(data=drive_inventory)
                drive_inventory_obj.is_valid(raise_exception=True)
                drive_inventory_obj.save()

    @staticmethod
    def create_drive_billing(drive_id,request_data):
        if request_data.get('drive_billings'):
            for drive_billing in request_data['drive_billings']:
                drive_billing.update({"drive":drive_id})
                drive_billing_obj = DriveBillingSerializer(data=drive_billing)
                drive_billing_obj.is_valid(raise_exception=True)
                drive_billing_obj.save()

    @staticmethod
    def update_drive_inventory(drive_id,request_data):
        if request_data.get('drive_inventories'):
            
            valid_drive_inventories = []
            
            for drive_inventory in request_data['drive_inventories']:
                
                drive_inventory.update({"drive":drive_id})

                if drive_inventory.get("id"):
                    drive_inventory_instance = DriveInventory.objects.get(id=drive_inventory.get("id"))
                    drive_inventory_obj = DriveInventorySerializer(drive_inventory_instance, data=drive_inventory, partial=True)
                    drive_inventory_obj.is_valid(raise_exception=True)
                    drive_inventory_obj.save()

                    valid_drive_inventories.append(drive_inventory.get("id"))
                else:
                    drive_inventory_obj = DriveInventorySerializer(data=drive_inventory)
                    drive_inventory_obj.is_valid(raise_exception=True)
                    drive_inventory_id = drive_inventory_obj.save()

                    valid_drive_inventories.append(drive_inventory_id.id)

            DriveInventory.objects.filter(drive_id=drive_id).exclude(id__in=valid_drive_inventories).delete()

    @staticmethod
    def update_drive_billing(drive_id,request_data):
        if request_data.get('drive_billings'):
            
            valid_drive_billings = []
            
            for drive_billing in request_data['drive_billings']:
                
                drive_billing.update({"drive":drive_id})

                if drive_billing.get("id"):
                    drive_billing_instance = DriveBilling.objects.get(id=drive_billing.get("id"))
                    drive_billing_obj = DriveBillingSerializer(drive_billing_instance, data=drive_billing, partial=True)
                    drive_billing_obj.is_valid(raise_exception=True)
                    drive_billing_obj.save()

                    valid_drive_billings.append(drive_billing.get("id"))
                else:
                    drive_billing_obj = DriveBillingSerializer(data=drive_billing)
                    drive_billing_obj.is_valid(raise_exception=True)
                    drive_billing_id = drive_billing_obj.save()

                    valid_drive_billings.append(drive_billing_id.id)

            DriveBilling.objects.filter(drive_id=drive_id).exclude(id__in=valid_drive_billings).delete()
            