from apps.patients.models import FamilyMember
from django.conf import settings
from apps.master_data.exceptions import InvalidDobFormatValidationException, InvalidDobValidationException
from apps.payments.razorpay_views import RazorDrivePayment
from apps.appointments.utils import cancel_and_refund_parameters
from django.db.models.query_utils import Q
from apps.additional_features.serializers import DriveBillingSerializer, DriveInventorySerializer
import logging
import random
import re
import string

from datetime import datetime,date
from utils.utils import calculate_age, end_date_vaccination_date_comparision, start_end_datetime_comparision
from apps.additional_features.models import Drive, DriveBilling, DriveBooking, DriveInventory
from rest_framework.serializers import ValidationError


logger = logging.getLogger("AdditionalFeaturesUtil")

class AdditionalFeaturesUtil:

    @staticmethod
    def generate_unique_booking_number():
        booking_number = ""
        while True:
            try:
                str_part = ''.join(random.choice(string.ascii_letters) for i in range(5)).upper()
                int_part = ''.join(random.choice(string.digits) for i in range(5))
                booking_number = str_part + int_part
                Drive.objects.get(booking_number=booking_number)
            except Exception as e:
                logger.debug("Exception generate_unique_booking_number: %s"%(str(e)))
                return booking_number
    
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

    @staticmethod
    def update_user_data(request,dob,aadhar_number,patient):
        user = None
        if request.data.get("family_member"):
            user = FamilyMember.objects.get(id=request.data.get("family_member"))
        else:
            user = patient
        user.dob = dob
        user.aadhar_number = aadhar_number
        user.save()

    @staticmethod
    def validate_patient_age(dob):
        dob_date = None
        try:
            dob_date = datetime.strptime(dob,"%Y-%m-%d")
        except Exception as e:
            logger.error("Error parsing date of birth! %s"%(str(e)))
            raise InvalidDobFormatValidationException
        if not dob_date or (calculate_age(dob_date)<settings.MIN_VACCINATION_AGE):
            raise InvalidDobValidationException

    @staticmethod
    def validate_if_the_drive_is_already_booked(request,drive_id,patient):
        if request.data.get("family_member"):
            is_already_booked = DriveBooking.objects.filter(
                                                Q(family_member__id=request.data.get("family_member")) &
                                                Q(drive__id=drive_id) &
                                                Q(status__in=[DriveBooking.BOOKING_PENDING,DriveBooking.BOOKING_BOOKED])
                                            )
        else:
            is_already_booked = DriveBooking.objects.filter(
                                                Q(patient__id=patient.id) &
                                                Q(drive__id=drive_id) &
                                                Q(status__in=[DriveBooking.BOOKING_PENDING,DriveBooking.BOOKING_BOOKED])
                                            )
        
        if is_already_booked.exists():
            raise ValidationError("You have already registered for the selected patient.")
    
    @staticmethod
    def validate_inventory(drive_inventory,drive_id):
        drive_inventories_consumed = DriveBooking.objects.filter(
                                            Q(drive_inventory=drive_inventory) &
                                            Q(drive__id=drive_id) &
                                            Q(status__in=[DriveBooking.BOOKING_PENDING,DriveBooking.BOOKING_BOOKED])
                                        ).count()
        
        item_quantity  = DriveInventory.objects.filter(id=drive_inventory).values_list('item_quantity',flat=True)[0]
        
        if drive_inventories_consumed >= item_quantity:
            raise ValidationError("Sorry! All vaccines are consumed for the selected vaccine, You can book with another Vaccine")

    @staticmethod
    def validate_and_prepare_payment_data(request,drive_booking,amount):

        validate_payment_request_data = {
            "location_code":drive_booking.drive.hospital.code,
            "drive_booking_id":str(drive_booking.id),
            "registration_payment":request.data.get('registration_payment',False),
            "account":{
                "amount": amount,
                "email":""
            }
        }

        validate_payment_response = RazorDrivePayment.as_view()(cancel_and_refund_parameters(validate_payment_request_data))

        logger.info("Response Data in DriveBookingViewSet -> perform_create : %s"%(str(validate_payment_response.data)))

        if validate_payment_response.status_code!=200:
            drive_booking.delete()
            raise ValidationError("Could not book drive for you.")