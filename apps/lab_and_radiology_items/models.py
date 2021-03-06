from apps.lab_and_radiology_items.constants import LabAndRadiologyItemsConstants
import os
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.validators import FileExtensionValidator
from django.db import models

from apps.appointments.models import CancellationReason
from apps.master_data.models import (BillingGroup, BillingSubGroup,
                                     HomeCareService, Hospital)
from apps.meta_app.models import MyBaseModel
from apps.patients.models import FamilyMember, Patient, PatientAddress
from utils.custom_storage import FileStorage
from utils.validators import validate_file_authenticity, validate_file_size
from django_clamd.validators import validate_file_infection


def generate_prescription_file_path(self, filename):
    _, obj_file_extension = os.path.splitext(filename)
    obj_name = str(self.id) + str(obj_file_extension)
    return "users/{0}/prescription/{1}".format(self.id, obj_name)


def generate_service_prescription_file_path(self, filename):
    _, obj_file_extension = os.path.splitext(filename)
    obj_name = str(self.id) + str(obj_file_extension)
    return "users/{0}/service_prescription/{1}".format(self.id, obj_name)


class LabRadiologyItem(MyBaseModel):

    code = models.SlugField(max_length=200,
                            unique=True,
                            blank=True,
                            null=True)

    description = models.CharField(max_length=300,
                                   null=False,
                                   blank=False,
                                   )

    billing_group = models.ForeignKey(BillingGroup,
                                      on_delete=models.PROTECT,
                                      null=True,
                                      blank=True)

    billing_sub_group = models.ForeignKey(
        BillingSubGroup,
        on_delete=models.PROTECT,
        null=True,
        blank=True)

    class Meta:
        verbose_name = "LabRadiology Item"
        verbose_name_plural = "LabRadiology Items"

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        super(LabRadiologyItem, self).save(*args, **kwargs)


class LabRadiologyItemPricing(MyBaseModel):

    item = models.ForeignKey(LabRadiologyItem,
                             related_name='lab_radiology_item_pricing',
                             on_delete=models.PROTECT,
                             null=False,
                             blank=False)

    hospital = models.ForeignKey(Hospital,
                                 on_delete=models.PROTECT,
                                 null=False,
                                 blank=False)

    price = models.IntegerField()

    start_date = models.DateField()

    end_date = models.DateField(null=True,
                                blank=True
                                )

    class Meta:
        verbose_name = "Health Test Pricing"
        verbose_name_plural = "Health Test Pricing"
        unique_together = [['item', 'hospital'], ]

    def __str__(self):
        return self.item.code

    def save(self, *args, **kwargs):
        super(LabRadiologyItemPricing, self).save(*args, **kwargs)


class PatientServiceAppointment(MyBaseModel):
    SERVICE_APPOINTMENT_STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        (LabAndRadiologyItemsConstants.IN_PROGRESS_CHOICE, LabAndRadiologyItemsConstants.IN_PROGRESS_CHOICE),
        ('Cancelled', 'Cancelled')


    )
    appointment_date = models.DateField()

    service = models.ForeignKey(HomeCareService,
                                null=False,
                                blank=False,
                                on_delete=models.PROTECT, related_name='patient_service_appointment')

    document = models.FileField(upload_to=generate_prescription_file_path,
                                storage=FileStorage(),
                                validators=[
                                            FileExtensionValidator(settings.VALID_FILE_EXTENSIONS), 
                                            validate_file_size,
                                            validate_file_authenticity,
                                            validate_file_infection
                                        ],
                                blank=True,
                                null=True)

    patient = models.ForeignKey(Patient,
                                null=True,
                                blank=True,
                                on_delete=models.PROTECT, related_name='patient_service_appointment')

    family_member = models.ForeignKey(FamilyMember,
                                      on_delete=models.PROTECT,
                                      related_name='family_service_appointment',
                                      blank=True,
                                      null=True)

    hospital = models.ForeignKey(Hospital,
                                 on_delete=models.PROTECT,
                                 null=True,
                                 blank=True)

    referenced_address = models.ForeignKey(PatientAddress, on_delete=models.SET_NULL,
                                           related_name='patient_service_appointment', null=True)

    status = models.CharField(choices=SERVICE_APPOINTMENT_STATUS_CHOICES,
                              default='Pending',
                              max_length=11
                              )

    reason = models.ForeignKey(CancellationReason,
                               on_delete=models.PROTECT,
                               null=True, blank=True)

    other_reason = models.TextField(blank=True,
                                    null=True,
                                    max_length=500)

    address = JSONField(null=True, blank=True)

    @property
    def is_cancellable(self):
        if self.appointment_date and ((self.appointment_date > datetime.now().date()) and (self.status != "Cancelled")):
            return True
        return False

    class Meta:
        verbose_name = "Patient Service Appointment"
        verbose_name_plural = "Patient Service Appointments"

    def __str__(self):
        return self.patient.first_name


class UploadPrescription(MyBaseModel):
    appointment_date = models.DateTimeField()

    patient = models.ForeignKey(Patient,
                                null=True,
                                blank=True,
                                on_delete=models.PROTECT, related_name='prescription')

    family_member = models.ForeignKey(FamilyMember,
                                      on_delete=models.PROTECT,
                                      related_name='family_prescription',
                                      blank=True,
                                      null=True)

    address = models.ForeignKey(PatientAddress, on_delete=models.PROTECT,
                                related_name='patient_prescription')

    class Meta:
        verbose_name = "Prescription"
        verbose_name_plural = "Prescriptions"

    def __str__(self):
        return self.patient.first_name


class HomeCollectionAppointment(MyBaseModel):
    HOME_COLLECTION_APPOINTMENT_STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        (LabAndRadiologyItemsConstants.IN_PROGRESS_CHOICE, LabAndRadiologyItemsConstants.IN_PROGRESS_CHOICE),
        ('Cancelled', 'Cancelled')
    )
    appointment_date = models.DateField()

    home_collections = models.ManyToManyField(LabRadiologyItem,
                                              blank=True)

    document = models.FileField(upload_to=generate_service_prescription_file_path,
                                storage=FileStorage(),
                                validators=[
                                            FileExtensionValidator(settings.VALID_FILE_EXTENSIONS), 
                                            validate_file_size,
                                            validate_file_authenticity,
                                            validate_file_infection
                                        ],
                                blank=True,
                                null=True)

    hospital = models.ForeignKey(Hospital,
                                 on_delete=models.PROTECT,
                                 null=True,
                                 blank=True)

    patient = models.ForeignKey(Patient,
                                null=True,
                                blank=True,
                                on_delete=models.PROTECT, related_name='patient_home_collection_appointment')

    family_member = models.ForeignKey(FamilyMember,
                                      on_delete=models.PROTECT,
                                      related_name='family_home_collection_appointment',
                                      blank=True,
                                      null=True)

    referenced_address = models.ForeignKey(PatientAddress, on_delete=models.SET_NULL,
                                           related_name='patient_home_collection_appointment', null=True)

    status = models.CharField(choices=HOME_COLLECTION_APPOINTMENT_STATUS_CHOICES,
                              default='Pending',
                              max_length=11
                              )

    reason = models.ForeignKey(CancellationReason,
                               on_delete=models.PROTECT,
                               null=True, blank=True)

    other_reason = models.TextField(blank=True,
                                    null=True,
                                    max_length=500)

    address = JSONField(null=True, blank=True)

    @property
    def is_cancellable(self):
        if self.appointment_date and ((self.appointment_date > datetime.now().date()) and (self.status != "Cancelled")):
            return True
        return False

    class Meta:
        verbose_name = "Home Collection Appointment"
        verbose_name_plural = "Home Collection Appointments"

    def __str__(self):
        return self.patient.first_name
