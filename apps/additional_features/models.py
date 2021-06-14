from datetime import datetime
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
    return "static/qr_code/{0}".format(obj_name)

class Drive(MyBaseModel):
    
    TYPE_CHOICES = (
        ('apartment','Apartment'),
        ('corporate','Corporate')
    )
    
    hospital = models.ForeignKey(
                        Hospital,
                        on_delete=models.PROTECT,
                        null=False,
                        blank=False
                    )
    
    description = models.TextField(
                                blank=False,
                                null=False
                            )
    
    type = models.CharField(
                        choices=TYPE_CHOICES,
                        max_length=100,
                        blank=False,
                        null=False
                    )
    
    domain = models.CharField(
                        max_length=100,
                        blank=True,
                        null=True       
                    )
    
    date = models.DateField(
                        auto_now=True,
                        blank=False,
                        null=False,
                    )
    
    booking_start_time = models.DateTimeField(
                                        default=datetime.now,
                                        blank=False,
                                        null=False,
                                    )
    
    booking_end_time = models.DateTimeField(
                                        default=datetime.now,
                                        blank=False,
                                        null=False,
                                    )
    
    code = models.SlugField(
                            unique=True,
                            blank=True,
                            null=True
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
                        blank=True,
                        null=True,
                        verbose_name='display_QR_code'
                    )
    
    is_active = models.BooleanField(default=True)
    
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
                                related_name="medicine_name"   
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
    
    item_quantity = models.IntegerField(
                                    blank=False,
                                    null=False,
                                    default=0
                                )    
    
    price = models.FloatField(default=0)
    
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

class DriveBooking(MyBaseModel):
    
    BOOKING_STATUS_CHOICES = (
        ("pending","Pending"),
        ("booked","Booked"),
        ("cancelled","Cancelled"),
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
                        max_length=15,
                        blank=False,
                        null=False,
                        default='pending'
                        )

class StaticInstructions(MyBaseModel):
    
    title = models.CharField(
                        max_length=50,
                        blank=True,
                        null=True
                    )
    
    instruction_type = models.CharField(
                                    max_length=50,
                                    blank=False,
                                    null=False
                                )
    
    instruction = models.TextField(
                            blank=False,
                            null=False
                        )
    
    sequence = models.IntegerField(
                            blank=False,
                            null=False
                        )
    