from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

# Create your models here.
from apps.meta_app.models import MyBaseModel


class Hospital(MyBaseModel):

    profit_center = models.CharField(max_length=50,
                                     null=False,
                                     blank=False,
                                     )

    code = models.SlugField(unique=True,
                            blank=True,
                            null=True)

    description = models.TextField(blank=True,
                                   null=True)

    email = models.EmailField()

    mobile = PhoneNumberField(blank=True,
                              null=True,
                              verbose_name="Mobile Number")

    address = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Hospital"
        verbose_name_plural = "Hospitals"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super(Hospital, self).save(*args, **kwargs)



class Specialisation(MyBaseModel):

    code = models.SlugField(unique=True,
                            blank=True,
                            null=True)

    description = models.TextField(blank=True,
                                   null=True)

    start_date = models.DateField()

    end_date = models.DateField()
    class Meta:
        verbose_name = "Specialisation"
        verbose_name_plural = "Specialisations"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super(Specialisation, self).save(*args, **kwargs)




class BillingGroup(MyBaseModel):

    name = models.CharField(max_length=50,
                            null=False,
                            blank=False,
                            )

    slug = models.SlugField(unique=True,
                            blank=True,
                            null=True)

    start_date = models.DateField()

    end_date = models.DateField()
    class Meta:
        verbose_name = "Billing Group"
        verbose_name_plural = "Billing Groups"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = self.name.lower().strip().replace(" ", "_")
        super(BillingGroup, self).save(*args, **kwargs)


class BillingSubGroup(MyBaseModel):

    name = models.CharField(max_length=50,
                            null=False,
                            blank=False,
                            )

    slug = models.SlugField(unique=True,
                            blank=True,
                            null=True)

    start_date = models.DateField()

    end_date = models.DateField()
    class Meta:
        verbose_name = "Billing Sub Group"
        verbose_name_plural = "Billing Sub Groups"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = self.name.lower().strip().replace(" ", "_")
        super(BillingSubGroup, self).save(*args, **kwargs)

