from django.db.models.deletion import PROTECT
from django.db.models.expressions import F
from apps.payments.models import Payment
import uuid
import os


from apps.patients.models import FamilyMember, Patient
from apps.users.models import BaseUser
from apps.master_data.models import Billing, Hospital, Medicine
from utils.validators import validate_file_authenticity, validate_file_size

from django.conf import settings
from django.core.validators import FileExtensionValidator
from utils.custom_storage import MediaStorage
from django_clamd.validators import validate_file_infection

from apps.meta_app.models import MyBaseModel
from django.db import models
    

def generate_qr_code_picture_path(self, filename):
    _, obj_file_extension = os.path.splitext(filename)
    obj_name = str(uuid.uuid4()) + str(obj_file_extension)
    return "static/flyers/{0}".format(obj_name)

class Drive(MyBaseModel):
    
    hospital = models.ForeignKey(
                        Hospital,
                        on_delete=models.PROTECT,
                        null=False,
                        blank=False
                    )
    
    description = models.TextField()
    
    type = models.CharField(
                            max_length=100,
                            blank=False,
                            null=False
                        )
    
    domain = models.CharField(
                        max_length=100,
                        blank=True,
                        null=True       
                    )
    
    date = models.DateField(blank=False,
                            null=False,)
    
    booking_start_time = models.DateTimeField()
    
    booking_end_time = models.DateTimeField()
    
    code = models.SlugField(
                            unique=True,
                            blank=False,
                            null=False
                        )
    
    qr_code = models.ImageField(
                        upload_to=generate_qr_code_picture_path,
                        storage=MediaStorage(),
                        validators=[
                            FileExtensionValidator(settings.VALID_IMAGE_FILE_EXTENSIONS), 
                            validate_file_size,
                            validate_file_authenticity,
                            validate_file_infection
                        ],
                        blank=False,
                        null=False,
                        verbose_name='display_QR_code'
                    )
    
    is_active = models.BooleanField(default=True)
    
    created_by = models.ForeignKey(
                            BaseUser,
                            on_delete=models.PROTECT,
                            null=True,
                            blank=True,
                            related_name = 'drive_created_by_base_user'
                        )

    updated_by = models.ForeignKey(
                            BaseUser,
                            on_delete=models.PROTECT,
                            null=True,
                            blank=True,
                            related_name = 'drive_updated_by_base_user'
                        )
    
class DriveInventory(MyBaseModel):
    
    drive = models.ForeignKey(
                            Drive,
                            on_delete=models.PROTECT,
                            null=False,
                            blank=False,
                            related_name = 'drive_schedule'
                        )
    
    medicine = models.ForeignKey(
                                Medicine,
                                on_delete=models.PROTECT,
                                blank=False,
                                null=False,
                                related_name="dose_name"   
                            )
    
    dose = models.CharField(
                        max_length=8,
                        blank=False,
                        null=False
                    )  
    
    mh_item_code = models.CharField(
                            max_length=100,
                            blank=False,
                            null=False
                        )
    
    item_quantity = models.IntegerField()
    
    price = models.FloatField(default=0)
    
    created_by = models.ForeignKey(
                            BaseUser,
                            on_delete=models.PROTECT,
                            null=True,
                            blank=True,
                            related_name = 'inventory_created_by_base_user'
                        )
    
    updated_by = models.ForeignKey(
                            BaseUser,
                            on_delete=models.PROTECT,
                            null=True,
                            blank=True,
                            related_name = 'inventory_updated_by_base_user'
                        )
    
class DriveBilling(MyBaseModel):
    
    drive = models.ForeignKey(
                        Drive,
                        on_delete=PROTECT,
                        blank=False,
                        null=False,
                        related_name='billing_drive_schedule'
                    )

    billing = models.ForeignKey(
                            Billing,
                            on_delete=PROTECT,
                            blank=False,
                            null=False,
                            related_name='drive_billing'
                        )
    price = models.FloatField(default=0)
    
    created_by = models.ForeignKey(
                            BaseUser,
                            on_delete=models.PROTECT,
                            null=True,
                            blank=True,
                            related_name = 'drive_billing_created_by_base_user'
                        )
    
    updated_by = models.ForeignKey(
                            BaseUser,
                            on_delete=models.PROTECT,
                            null=True,
                            blank=True,
                            related_name = 'drive_billing_updated_by_base_user'
                        )

class DriveBooking(MyBaseModel):
    
    BOOKING_STATUS_CHOICES = (
        ("Pending","Pending"),
        ("Booked","Booked"),
        ("Cancelled","Cancelled"),
    )
        
    drive = models.ForeignKey(
                            Drive,
                            on_delete=models.PROTECT,
                            null=False,
                            blank=False,
                            related_name = 'booking_drive_schedule'
                        )
    
    drive_inventory = models.ForeignKey(
                                    DriveInventory,
                                    on_delete=models.PROTECT,
                                    blank=False,
                                    null=False,
                                    related_name="booking_drive_inventory"
                                )
    
    patient = models.ForeignKey(
                            Patient,
                            on_delete=models.PROTECT,
                            null=False,
                            blank=False,
                            related_name = 'patient_vaccine_registration'
                        )
    
    family_member = models.ForeignKey(
                                    FamilyMember,
                                    on_delete=models.PROTECT,
                                    null=True,
                                    blank=True,
                                    related_name = 'family_member_vaccine_registration'
                                )
    
    payment = models.ForeignKey(
                            Payment,
                            on_delete=models.PROTECT,
                            null=True,
                            blank=True,
                            related_name = 'booking_payment'
                        )
    
    booking_number = models.CharField(
                                max_length=10,
                                blank=False,
                                null=False
                            )
    
    status = models.CharField(
                        choices=BOOKING_STATUS_CHOICES,
                        max_length=15
                        )
    
    created_by = models.ForeignKey(
                            BaseUser,
                            on_delete=models.PROTECT,
                            null=True,
                            blank=True,
                            related_name = 'drive_booking_created_by_base_user'
                        )
    
    updated_by = models.ForeignKey(
                            BaseUser,
                            on_delete=models.PROTECT,
                            null=True,
                            blank=True,
                            related_name = 'drive_booking_updated_by_base_user'
                        )

class StaticInstructions(MyBaseModel):
    instruction_type = models.CharField(
                                    max_length=50,
                                    blank=False,
                                    null=False
                                )
    
    instruction = models.TextField()
    
    sequence = models.IntegerField()
    