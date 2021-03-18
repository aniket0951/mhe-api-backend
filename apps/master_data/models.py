import os
from django.contrib.gis.geos import Point
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from apps.meta_app.models import MyBaseModel
from django.contrib.gis.db import models

from utils.custom_storage import FileStorage, MediaStorage
from utils.validators import validate_file_authenticity, validate_file_size
from django.core.validators import FileExtensionValidator
from django.conf import settings


def generate_service_file_path(self, filename):
    _, obj_file_extension = os.path.splitext(filename)
    obj_name = str(self.name) + str(obj_file_extension)
    return "home_services/{0}".format(obj_name)

class Hospital(MyBaseModel):

    code = models.SlugField(unique=True,
                            blank=False,
                            null=False)

    description = models.TextField(blank=False,
                                   null=False,
                                   max_length=100)

    email = models.EmailField()

    mobile = PhoneNumberField(blank=True,
                              null=True,
                              verbose_name="Mobile Number")

    address = models.TextField(blank=True,
                               null=True,
                               max_length=100)

    location = models.PointField(default=Point(1, 1),
                                 null=True, blank=True,)

    is_home_collection_supported = models.BooleanField(default=False)

    is_health_package_online_purchase_supported = models.BooleanField(
        default=False)

    health_package_doctor_code = models.CharField(max_length=10,
                                                  null=True,
                                                  blank=True,)
    health_package_department_code = models.CharField(max_length=10,
                                                      null=True,
                                                      blank=True,)

    corporate_only = models.BooleanField(default=False)

    hospital_enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Hospital"
        verbose_name_plural = "Hospitals"

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        super(Hospital, self).save(*args, **kwargs)


class Department(MyBaseModel):

    code = models.SlugField(max_length=200,
                            unique=True,
                            blank=True,
                            null=True)

    name = models.CharField(max_length=200,
                            null=True,
                            blank=True,)

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        super(Department, self).save(*args, **kwargs)


class HospitalDepartment(MyBaseModel):

    hospital = models.ForeignKey(Hospital,
                                 on_delete=models.PROTECT,
                                 )

    department = models.ForeignKey(Department,
                                   on_delete=models.PROTECT,
                                   )
    start_date = models.DateField()

    end_date = models.DateField(null=True,
                                blank=True
                                )

    class Meta:
        verbose_name = "Hospital Department"
        verbose_name_plural = "Hospital Department"

    def __str__(self):
        return self.hospital.code

    def save(self, *args, **kwargs):
        super(HospitalDepartment, self).save(*args, **kwargs)


class Specialisation(MyBaseModel):

    code = models.SlugField(max_length=200,
                            unique=True,
                            blank=True,
                            null=True)

    description = models.CharField(max_length=200,
                                   null=True,
                                   blank=True,)

    start_date = models.DateField()

    end_date = models.DateField(null=True,
                                blank=True
                                )

    class Meta:
        verbose_name = "Specialisation"
        verbose_name_plural = "Specialisations"

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        super(Specialisation, self).save(*args, **kwargs)


class BillingGroup(MyBaseModel):

    code = models.SlugField(unique=True,
                            blank=True,
                            null=True)

    code_abbreviation = models.CharField(max_length=100,
                                         null=True,
                                         blank=True,)

    description = models.TextField(blank=False,
                                   null=False,
                                   max_length=100)

    start_date = models.DateField(blank=False,
                                  null=False,)

    end_date = models.DateField(blank=True,
                                null=True)

    class Meta:
        verbose_name = "Billing Group"
        verbose_name_plural = "Billing Groups"

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        super(BillingGroup, self).save(*args, **kwargs)


class BillingSubGroup(MyBaseModel):

    code = models.SlugField(unique=True,
                            blank=True,
                            null=True)

    code_abbreviation = models.CharField(max_length=100,
                                         null=True,
                                         blank=True,)

    code_translation = models.CharField(max_length=100,
                                        null=True,
                                        blank=True,)

    description = models.TextField(blank=False,
                                   null=False,
                                   max_length=100)

    billing_group = models.ForeignKey(BillingGroup,
                                      on_delete=models.PROTECT,
                                      )

    start_date = models.DateField(blank=False,
                                  null=False,)

    end_date = models.DateField(blank=True,
                                null=True)

    class Meta:
        verbose_name = "Billing Sub Group"
        verbose_name_plural = "Billing Sub Groups"

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        super(BillingSubGroup, self).save(*args, **kwargs)


class HomeCareService(MyBaseModel):

    name = models.CharField(max_length=200,
                            null=True,
                            blank=True,)
    
    image = models.ImageField(upload_to=generate_service_file_path,
                                storage=MediaStorage(),
                                validators=[FileExtensionValidator(
                                            settings.VALID_IMAGE_FILE_EXTENSIONS), validate_file_size,
                                            validate_file_authenticity],
                                blank=True,
                                null=True)


    class Meta:
        verbose_name = "Home Care Service"
        verbose_name_plural = "Home Care Services"

    def __str__(self):
        return self.name

class AmbulanceContact(MyBaseModel):

    hospital = models.ForeignKey(Hospital,
                                 on_delete=models.PROTECT,
                                 )

    mobile = PhoneNumberField(blank=True,
                              null=True,
                              verbose_name="Mobile Number")
    
    class Meta:
        verbose_name = "Ambulance Contact"
        verbose_name_plural = "Ambulance Contacts"

class Components(MyBaseModel):

    name = models.CharField(max_length=50,
                            null=False,
                            blank=False)

    is_active = models.BooleanField(default=True)

class CompanyDomain(MyBaseModel):

    domain = models.CharField(max_length=30,
                            null=False,
                            blank=False)

    is_active = models.BooleanField(default=True)
class Company(MyBaseModel):

    name = models.SlugField(unique=True,
                            blank=False,
                            null=False)

    domain = models.CharField(max_length=30,
                            null=True,
                            blank=True)

    hospital_info = models.ManyToManyField(Hospital,
                                             blank=True,
                                             null=True,
                                             related_name='company_hospital')
    
    component_ids = models.ManyToManyField(Components, blank=True,
                                             null=True,related_name='allowed_components')

    is_active = models.BooleanField(default=True)

class EmergencyContact(MyBaseModel):

    mobile = PhoneNumberField(blank=True,
                              null=True,
                              verbose_name="Emergency Number")
    
    class Meta:
        verbose_name = "Emergency Contact"
        verbose_name_plural = "Emergency Contacts"

class FeedbackRecipients(MyBaseModel):

    RECIPIENTS_TYPE = (
        ("TO", 'TO'),
        ("CC", 'CC'),
        ("BCC", 'BCC')
    )

    hospital_code = models.SlugField(
                                    unique=False,
                                    blank=False,
                                    null=False
                                )
    name = models.CharField(
                            max_length=50,
                            blank=True,
                            null=True
                        )
    contact = models.CharField(
                            max_length=20,
                            blank=True,
                            null=True
                        )
    type = models.CharField(
                            max_length=20,
                            choices=RECIPIENTS_TYPE,
                            blank=True,
                            null=True
                        )
    email = models.CharField(
                            max_length=50,
                            blank=True,
                            null=True
                        )
    class Meta:
        verbose_name = "Feedback recipient"
        verbose_name_plural = "Feedback recipients"