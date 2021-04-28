import os
import uuid

from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.contrib.postgres.fields import JSONField
from django.core.validators import (
                                FileExtensionValidator, 
                                MaxValueValidator,
                                MinValueValidator
                            )
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from apps.master_data.models import Hospital, Company
from apps.meta_app.models import AutoIncrementBaseModel, MyBaseModel
from apps.patient_registration.models import Relation
from apps.users.models import BaseUser
from utils.custom_storage import MediaStorage
from utils.validators import validate_file_authenticity, validate_file_size
import datetime


def generate_display_picture_path(self, filename):
    _, obj_file_extension = os.path.splitext(filename)
    obj_name = str(self.id) + str(obj_file_extension)
    return "users/{0}/profile_picture/{1}".format(self.id, obj_name)


def generate_family_member_display_picture_path(self, filename):
    _, obj_file_extension = os.path.splitext(filename)
    obj_name = str(uuid.uuid4()) + str(obj_file_extension)
    return "users/{0}/family_member/profile_picture/{1}".format(self.id, obj_name)


class Patient(BaseUser):
    GENDER_CHOICES = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Others', 'Others')
    )

    uhid_number = models.SlugField(unique=True,
                                   blank=True,
                                   null=True)

    pre_registration_number = models.CharField(max_length=20,
                                               blank=True,
                                               null=True)

    first_name = models.CharField(max_length=200,
                                  blank=False,
                                  null=False,
                                  verbose_name='First Name')

    last_name = models.CharField(max_length=200,
                                 blank=True,
                                 null=True,
                                 verbose_name='Last Name')

    middle_name = models.CharField(max_length=200,
                                   blank=True,
                                   null=True,
                                   verbose_name='Middle Name')

    facebook_id = models.CharField(blank=True,
                                   null=True,
                                   max_length=100,
                                   verbose_name="Facebook Id")

    google_id = models.CharField(blank=True,
                                 null=True,
                                 max_length=100,
                                 verbose_name="Google Id")

    apple_id = models.CharField(blank=True,
                                null=True,
                                max_length=100,
                                verbose_name="Apple Id")

    display_picture = models.ImageField(upload_to=generate_display_picture_path,
                                        storage=MediaStorage(),
                                        validators=[FileExtensionValidator(
                                            settings.VALID_IMAGE_FILE_EXTENSIONS), validate_file_size,
                                            validate_file_authenticity],
                                        blank=True,
                                        null=True,
                                        verbose_name='Profile Picture')

    email = models.EmailField(null=True,
                              blank=True)

    apple_email = models.EmailField(null=True,
                                    blank=True)

    email_otp = models.CharField(max_length=6,
                                 null=True,
                                 blank=True)

    otp_expiration_time = models.DateTimeField(
                                        blank=True,
                                        null=True,
                                        verbose_name='OTP Key Expiration DateTime')

    email_otp_expiration_time = models.DateTimeField(
                                            blank=True,
                                            null=True,
                                            verbose_name='Email OTP Key Expiration DateTime')

    gender = models.CharField(choices=GENDER_CHOICES,
                              blank=True,
                              null=True,
                              max_length=6,
                              verbose_name='Gender')

    age = models.IntegerField(blank=True, null=True)

    address = models.TextField(blank=True, null=True)

    mobile_verified = models.BooleanField(default=False,
                                          verbose_name='Mobile Verified')

    email_verified = models.BooleanField(default=False,
                                         verbose_name='Email Verified')

    favorite_hospital = models.ForeignKey(Hospital,
                                          on_delete=models.PROTECT,
                                          blank=True,
                                          null=True)

    new_mobile = PhoneNumberField(blank=True,
                                  null=True,
                                  verbose_name="New Mobile Number")

    new_mobile_verification_otp = models.CharField(blank=True, null=True,
                                                   max_length=10)

    new_mobile_otp_expiration_time = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='New mobile OTP Key Expiration DateTime')

    company_info = models.ForeignKey(Company,
                                     on_delete=models.PROTECT,
                                     null=True,
                                     blank=True,
                                     related_name='patient_company_info')

    corporate_email = models.EmailField(null=True, blank=True)

    corporate_email_otp = models.CharField(max_length=6,
                                           null=True,
                                           blank=True)

    corporate_email_otp_expiration_time = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Corporatse Email OTP Key Expiration DateTime')

    active_view = models.CharField(default="Normal",
                                   max_length=20)

    is_corporate = models.BooleanField(default=False,
                                       verbose_name='is_corporate')

    aadhar_number = models.BigIntegerField(
        validators=[MinValueValidator(100000000000), MaxValueValidator(999999999999)],
        blank=True,
        null=True
    )

    dob     = models.DateField(
        blank=True,
        null=True,
        verbose_name='Date of birth'
    )

    @property
    def representation(self):
        return 'Unique Manipal Identifier: {} Name: {}'.format(self.uhid_number, self.first_name)

    class Meta:
        verbose_name = "Patient"
        verbose_name_plural = "Patients"
        permissions = ()

    def __str__(self):
        return self.representation

    def save(self, *args, **kwargs):
        if self.__class__.objects.filter(pk=self.pk).exists():
            self._uhid_updated = False
            if self.uhid_number and not self.__class__.objects.filter(pk=self.pk).first().uhid_number:
                self._uhid_updated = True
        super().save(*args, **kwargs)

class FamilyMember(MyBaseModel):

    GENDER_CHOICES = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Others', 'Others')
    )

    patient_info = models.ForeignKey(Patient,
                                     on_delete=models.PROTECT,
                                     null=False,
                                     blank=False,
                                     related_name='patient_family_member_info')

    relationship = models.ForeignKey(Relation,
                                     on_delete=models.PROTECT,
                                     null=True,
                                     blank=True,
                                     related_name='patient_family_member_relation')

    mobile = PhoneNumberField(blank=True,
                              null=True,
                              verbose_name="Mobile Number")

    new_mobile = PhoneNumberField(blank=True,
                                  null=True,
                                  verbose_name="New Mobile Number")

    uhid_number = models.CharField(max_length=20,
                                   blank=True,
                                   null=True)

    pre_registration_number = models.CharField(max_length=20,
                                               blank=True,
                                               null=True)

    first_name = models.CharField(max_length=200,
                                  blank=True,
                                  null=True,
                                  verbose_name='First Name')

    last_name = models.CharField(max_length=200,
                                 blank=True,
                                 null=True,
                                 verbose_name='Last Name')

    middle_name = models.CharField(max_length=200,
                                   blank=True,
                                   null=True,
                                   verbose_name='Middle Name')

    display_picture = models.ImageField(upload_to=generate_family_member_display_picture_path,
                                        storage=MediaStorage(),
                                        validators=[FileExtensionValidator(
                                            settings.VALID_IMAGE_FILE_EXTENSIONS), validate_file_size,
                                            validate_file_authenticity],
                                        blank=True,
                                        null=True,
                                        verbose_name='Display Picture')

    gender = models.CharField(choices=GENDER_CHOICES,
                              blank=True,
                              null=True,
                              max_length=6,
                              verbose_name='Gender')

    age = models.IntegerField(blank=True, null=True)

    email = models.EmailField(null=True,
                              blank=True)

    mobile_verified = models.BooleanField(default=False,
                                          verbose_name='Mobile Verified')

    email_verified = models.BooleanField(default=False,
                                         verbose_name='Email Verified')

    is_visible = models.BooleanField(default=False)

    is_corporate = models.BooleanField(default=False,
                                       verbose_name='is_corporate')
    
    raw_info_from_manipal_API = JSONField(blank=True,
                                          null=True
                                          )

    mobile_verification_otp = models.CharField(blank=True, null=True,
                                               max_length=10)

    email_verification_otp = models.CharField(blank=True, null=True,
                                              max_length=10)

    mobile_otp_expiration_time = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Mobile OTP Key Expiration DateTime')

    email_otp_expiration_time = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Email OTP Key Expiration DateTime')
    
    aadhar_number = models.BigIntegerField(
        validators=[MinValueValidator(100000000000), MaxValueValidator(999999999999)],
        blank=True,
        null=True
    )

    dob     = models.DateField(
        blank=True,
        null=True,
        verbose_name='Date of birth'
    )

    @property
    def representation(self):
        return 'Patient name: {} Patient family member name: {}'\
            .format(self.patient_info.first_name, self.first_name)

    class Meta:
        verbose_name = "Family Member"
        verbose_name_plural = "Family Members"

    def __str__(self):
        return self.representation

    def save(self, *args, **kwargs):
        if self.__class__.objects.filter(pk=self.pk).exists():
            self._uhid_updated = False
            if self.uhid_number and not self.__class__.objects.filter(pk=self.pk).first().uhid_number:
                self._uhid_updated = True
        super().save(*args, **kwargs)

class FamilyMemberCorporateHistory(MyBaseModel):

    family_member = models.ForeignKey(FamilyMember,
                                        on_delete=models.PROTECT,
                                        null=False,
                                        blank=False,
                                        related_name='patient_family_member_corporate_history')

    company_info = models.ForeignKey(Company,
                                        on_delete=models.PROTECT,
                                        null=False,
                                        blank=False,
                                        related_name='patient_family_member_company_info')

class PatientAddress(MyBaseModel):
    ADDRESS_CHOICES = (
        ('Home Address', 'Home Address'),
        ('Work/Office Address', 'Work/Office Address')
    )

    pincode_number = models.PositiveIntegerField(
        validators=[MinValueValidator(100000), MaxValueValidator(999999)],
        blank=False,
        null=False)

    house_details = models.CharField(max_length=500,
                                     blank=False,
                                     null=False)

    area_details = models.CharField(max_length=500,
                                    blank=False,
                                    null=False)

    address_type = models.CharField(choices=ADDRESS_CHOICES,
                                    blank=True,
                                    null=True,
                                    max_length=20,
                                    default="Home Address"
                                    )

    patient_info = models.ForeignKey(Patient,
                                     on_delete=models.PROTECT,
                                     null=True,
                                     blank=True,
                                     related_name='patient_address_info')

    location = gis_models.PointField(
        default=Point(1, 1), null=True, blank=True,)

    @property
    def representation(self):
        return 'Patient name {}'.format(self.patient_info.first_name)

    class Meta:
        verbose_name = "Patient Address"
        verbose_name_plural = "Patient Addresses"

    def __str__(self):
        return self.representation

class OtpGenerationCount(MyBaseModel):

    mobile = PhoneNumberField(blank=True,
                              null=True,
                              verbose_name="Mobile Number")

    otp_generation_count = models.IntegerField(default = 0, blank=True, null=True)

    class Meta:
        verbose_name = "Patient Otp Count"
        verbose_name_plural = "Patient Otp Counts"

class WhiteListedToken(models.Model):
    token = models.CharField(max_length=500)
    user = models.ForeignKey(BaseUser, related_name="token_user", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("token", "user")

class CovidVaccinationRegistration(AutoIncrementBaseModel):

    PAYMENT_PENDING = 'payment_pending'
    REQUESTED       = 'requested'
    SCHEDULED       = 'scheduled'
    COMPLETED       = 'completed'
    CANCELLED       = 'cancelled'

    STATUS_CHOICES = (
        (PAYMENT_PENDING,   'Payment Pending'),
        (REQUESTED,         'Requested'),
        (SCHEDULED,         'Scheduled'),
        (COMPLETED,         'Completed'),
        (CANCELLED,         'Cancelled')
    )

    DOSE_1 = "1"
    DOSE_2 = "2"

    DOSE_TYPE_CHOICE = (
        (DOSE_1,DOSE_1),
        (DOSE_2,DOSE_2),
    )

    preferred_hospital = models.ForeignKey(
                        Hospital, 
                        on_delete = models.PROTECT, 
                        related_name = 'hospital_covid_registration'
                    )
    vaccination_date= models.DateField(
                        blank=True,
                        null=True,
                        verbose_name='Date of vaccination'
                    )
    vaccination_slot = models.TimeField(
                        blank=True,
                        null=True,
                        verbose_name='Time slot of vaccination'
                    )
    status          = models.CharField(
                        choices=STATUS_CHOICES,
                        default=PAYMENT_PENDING,
                        max_length=30
                    )
    dose_type       = models.CharField(
                        choices=DOSE_TYPE_CHOICE,
                        default=DOSE_1,
                        max_length=10
                    )
    patient         = models.ForeignKey(
                        Patient, 
                        on_delete = models.PROTECT, 
                        related_name = 'patient_covid_registration'
                    )
    family_member   = models.ForeignKey(
                        FamilyMember, 
                        on_delete = models.PROTECT, 
                        related_name = 'family_member_covid_registration',
                        null=True
                    )
    remarks         = models.TextField(
                        null=True,
                        blank=True
                    )

    