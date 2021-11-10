import os
from django.db import models
from django.conf import settings

from phonenumber_field.modelfields import PhoneNumberField
from apps.appointments.models import CancellationReason
from apps.master_data.models import BillingGroup, BillingSubGroup, Hospital
from apps.meta_app.models import MyBaseModel
from apps.patients.models import FamilyMember, Patient, PatientAddress
from apps.payments.models import Payment
from apps.phlebo.models import Phlebo
from django.contrib.postgres.fields import JSONField
from django.core.validators import FileExtensionValidator
from utils.custom_storage import FileStorage
from utils.validators import validate_file_authenticity, validate_file_size
from django_clamd.validators import validate_file_infection

def generate_prescription_file_path(self, filename):
    _, obj_file_extension = os.path.splitext(filename)
    obj_name = str(self.id) + str(obj_file_extension)
    return "home_care/{0}/prescriptions/{1}".format(self.id, obj_name)

class HealthTestCategory(MyBaseModel):
    
    code = models.SlugField(
                        max_length=200,
                        unique=True,
                        blank=True,
                        null=True
                    )
    
    name = models.CharField(max_length=200)
    
class HealthTest(MyBaseModel):
    
    code = models.SlugField(
                        max_length=200,
                        unique=True,
                        blank=True,
                        null=True
                    )

    description = models.CharField(
                            max_length=300,
                            null=False,
                            blank=False,
                        )

    billing_group = models.ForeignKey(
                                BillingGroup,
                                on_delete=models.PROTECT,
                                null=True,
                                blank=True,
                                related_name='home_care_billing_group'
                            )

    billing_sub_group = models.ForeignKey(
                                    BillingSubGroup,
                                    on_delete=models.PROTECT,
                                    null=True,
                                    blank=True,
                                    related_name='home_care_billing_sub_group'
                                ) 
    
    health_test_category = models.ForeignKey(
                                    HealthTestCategory, 
                                    on_delete=models.PROTECT, 
                                    related_name='heath_test_category'
                                )

    class Meta:
        verbose_name = "Home Care"
        verbose_name_plural = "Home Care"

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        super(HealthTest, self).save(*args, **kwargs)


class HealthTestPricing(MyBaseModel):

    health_test = models.ForeignKey(
                                HealthTest,
                                on_delete=models.PROTECT,
                                null=False,
                                blank=False,
                                related_name='health_test'
                            )

    hospital = models.ForeignKey(
                                Hospital,
                                 on_delete=models.PROTECT,
                                 null=False,
                                 blank=False,
                                 related_name='health_test_hospital'
                            )

    price = models.IntegerField()

    start_date = models.DateField()

    end_date = models.DateField(null=True,
                                blank=True
                                )

    class Meta:
        verbose_name = "Health Test Pricing"
        verbose_name_plural = "Health Test Pricing"
        unique_together = [['health_test', 'hospital'], ]

    def __str__(self):
        return self.health_test.code

    def save(self, *args, **kwargs):
        super(HealthTestPricing, self).save(*args, **kwargs)

class HealthTestCartItems(MyBaseModel):
    
    health_test = models.ManyToManyField(HealthTest)
    
    hospital = models.ForeignKey(
                            Hospital, 
                            on_delete=models.PROTECT
                        )
    
    patient = models.OneToOneField(
                            Patient, 
                            on_delete=models.PROTECT, 
                            related_name='patient_user'
                        )

class LabTestAppointment(MyBaseModel):
    
    hospital = models.ForeignKey(
                            Hospital, 
                            on_delete=models.PROTECT,
                            blank = False,
                            null = False
                        )
    
    health_tests = models.ForeignKey(
                                HealthTest, 
                                on_delete=models.PROTECT,
                                blank = False,
                                null = False
                            )
    
    health_tests_origin = JSONField()
    
    patient = models.ForeignKey(
                            Patient, 
                            on_delete=models.PROTECT,
                            blank = False,
                            null = False
                        )
    
    family_member = models.ForeignKey(
                                FamilyMember, 
                                on_delete=models.PROTECT,
                                blank = True,
                                null = True
                            )
    
    payment = models.ForeignKey(
                            Payment, 
                            on_delete=models.PROTECT
                        )
    
    reason = models.ForeignKey(
                            CancellationReason, 
                            on_delete=models.PROTECT,
                            null=True, 
                            blank=True
                        )
    
    address = models.ForeignKey(
                            PatientAddress, 
                            on_delete=models.PROTECT
                        )
    
    phlebo = models.ForeignKey(
                            Phlebo, 
                            on_delete=models.PROTECT,
                            null=False, 
                            blank=False
                        )
    
    order_id = models.CharField(
                            max_length=50, 
                            unique=True
                        )
    
    distance = models.FloatField()
    
    other_reason = models.TextField(null=True, blank=True)
    
    appointment_date = models.DateTimeField()
    
    appointment_identifier = models.CharField(
                                        max_length=50,
                                        null=True, 
                                        blank=True
                                    )
    
    appointment_status = models.CharField(max_length=15)
    
    phlebo_status = models.CharField(max_length=15)
    
    prescription = models.FileField(upload_to=generate_prescription_file_path,
                                    storage=FileStorage(),
                                    validators=[
                                        FileExtensionValidator(settings.VALID_FILE_EXTENSIONS), 
                                        validate_file_size,
                                        validate_file_authenticity,
                                        validate_file_infection
                                    ],
                                    blank=False,
                                    null=False)
    
    booked_via_app = models.BooleanField(default=True)
     
class HospitalRegion(MyBaseModel):
    
    hospital = models.ForeignKey(
                            Hospital, 
                            on_delete=models.PROTECT,
                            blank = False,
                            null = False
                        )
    
    pin = models.CharField(max_length=20)
    
class LabTestSlotsMaster(MyBaseModel):
    slot_from = models.TimeField()
    slot_to = models.TimeField()

class LabTestSlotsWeeklyMaster(MyBaseModel):
    
    hospital = models.ForeignKey(
                            Hospital, 
                            on_delete=models.PROTECT,
                            blank = False,
                            null = False
                        )
    
    slot = models.ForeignKey(
                        LabTestSlotsMaster, 
                        on_delete=models.PROTECT,
                        blank = False,
                        null = False
                    )
     
    day = models.CharField(max_length=20)

class LabTestSlotSchedule(MyBaseModel):
    hospital = models.ForeignKey(
                            Hospital, 
                            on_delete=models.PROTECT,
                            blank = False,
                            null = False
                        )
    
    weekly_slot = models.ForeignKey(
                                LabTestSlotsWeeklyMaster, 
                                on_delete=models.PROTECT,
                                blank = False,
                                null = False
                            )
    
    phlebo = models.ForeignKey(
                            Phlebo, 
                            on_delete=models.PROTECT,
                            blank = False,
                            null = False
                        )
    
    pin = models.CharField(max_length=20)
    
class LabTestAppointmentHistory(MyBaseModel):
    appointment = models.ForeignKey(LabTestAppointment, on_delete=models.PROTECT)
    phlebo = models.ForeignKey(Phlebo, on_delete=models.PROTECT)
    appointment_status = models.CharField(max_length=50)
    phlebo_status = models.CharField(max_length=50)