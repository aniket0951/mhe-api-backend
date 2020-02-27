import os
import uuid

from django.contrib.postgres.fields import JSONField
from django.core.validators import FileExtensionValidator
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from apps.master_data.models import Hospital
from apps.meta_app.models import MyBaseModel
from apps.users.models import BaseUser
from manipal_api.settings import VALID_FILE_EXTENSIONS
from utils.custom_storage import LocalFileStorage, MediaStorage
from utils.validators import validate_file_authenticity, validate_file_size


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

    display_picture = models.ImageField(upload_to=generate_display_picture_path,
                                        storage=MediaStorage(),
                                        validators=[FileExtensionValidator(
                                            VALID_FILE_EXTENSIONS), validate_file_size,
                                            validate_file_authenticity],
                                        blank=True,
                                        null=True,
                                        verbose_name='Profile Picture')

    email = models.EmailField(null=False,
                              blank=False)

    otp_expiration_time = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='OTP Key Expiration DateTime')

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

    is_primary_account = models.BooleanField(default=False)

    favorite_hospital = models.ForeignKey(Hospital,
                                          on_delete=models.PROTECT,
                                          blank=True,
                                          null=True)

    @property
    def representation(self):
        return 'Unique Manipal Identifier: {} Name: {}'.format(self.uhid_number, self.first_name)

    class Meta:
        verbose_name = "Patient"
        verbose_name_plural = "Patients"
        permissions = ()

    def __str__(self):
        return self.representation


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

    relation_name = models.CharField(blank=False,
                                     max_length=100,
                                     null=False,
                                     verbose_name='Relation name',
                                     )

    mobile = PhoneNumberField(blank=True,
                              null=True,
                              verbose_name="Mobile Number")

    uhid_number = models.CharField(max_length=20,
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
                                            VALID_FILE_EXTENSIONS), validate_file_size,
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

    raw_info_from_manipal_API = JSONField(blank=True,
                                          null=True
                                          )

    @property
    def representation(self):
        return 'Patient name: {} Patient family member name: {} Relation Name: {}'\
            .format(self.patient_info.first_name, self.first_name,
                    self.relation_name)

    class Meta:
        verbose_name = "Family Member"
        verbose_name_plural = "Family Members"
        # unique_together = [['uhid_number', 'patient_info'], ]

    def __str__(self):
        return self.representation


class PatientUHID(MyBaseModel):

    patient_info = models.ForeignKey(Patient,
                                     on_delete=models.PROTECT,
                                     null=False,
                                     blank=False)

    uhid_number = models.CharField(max_length=20,
                                   blank=False,
                                   null=False)

    otp_expiration_time = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='OTP Key Expiration DateTime')

    @property
    def representation(self):
        return 'Patient name: {} UHID: {}'\
            .format(self.patient_info.first_name, self.uhid_number)

    class Meta:
        verbose_name = "Patient UHID"
        verbose_name_plural = "Patient UHIDs"

    def __str__(self):
        return self.representation
