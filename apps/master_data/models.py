from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point

from apps.meta_app.models import MyBaseModel
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
    location = models.PointField(default = Point(1, 1),null=True, blank=True,)
    

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
