from apps.health_packages.constants import HealthPackagesConstants
from django.db import models

from apps.health_tests.models import HealthTest
from apps.master_data.models import (BillingGroup, BillingSubGroup, Hospital,
                                     Specialisation)
from apps.meta_app.models import MyBaseModel


class HealthPackage(MyBaseModel):
    GENDER_CHOICES = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        (HealthPackagesConstants.MALE_AND_FEMALE_CHOICE, HealthPackagesConstants.MALE_AND_FEMALE_CHOICE)
    )

    code = models.SlugField(unique=True,
                            blank=True,
                            null=True)

    name = models.CharField(max_length=200,
                            null=False,
                            blank=False,
                            )

    description = models.TextField(max_length=1000, blank=True, null=True)

    benefits = models.TextField(max_length=1000, blank=True, null=True)

    age_from = models.IntegerField(default=0)

    age_to = models.IntegerField(default=120)

    gender = models.CharField(choices=GENDER_CHOICES,
                              default=HealthPackagesConstants.MALE_AND_FEMALE_CHOICE,
                              max_length=15,
                              verbose_name='Gender')

    specialisation = models.ForeignKey(Specialisation,
                                       related_name='health_package',
                                       on_delete=models.PROTECT,
                                       null=True,
                                       blank=True)

    included_health_tests = models.ManyToManyField(HealthTest,
                                                   related_name='health_package'
                                                   )

    is_popular = models.BooleanField(default=False,
                                     verbose_name='Popular Health Package')

    image = models.URLField(max_length=300,
                            null=True,
                            blank=True,
                            )

    class Meta:
        verbose_name = "Health Package"
        verbose_name_plural = "Health Packages"

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        super(HealthPackage, self).save(*args, **kwargs)


class HealthPackagePricing(MyBaseModel):

    health_package = models.ForeignKey(
        HealthPackage,
        related_name='health_package_pricing',
        on_delete=models.PROTECT,
        null=False,
        blank=False)

    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.PROTECT,
        null=False,
        blank=False)

    price = models.IntegerField()

    start_date = models.DateField(null=True,
                                blank=True)

    end_date = models.DateField(null=True,
                                blank=True
                                )

    discount_percentage = models.IntegerField(default=0)

    discount_start_date = models.DateField(null=True,
                                         blank=True)

    discount_end_date = models.DateField(null=True,
                                         blank=True
                                         )

    class Meta:
        verbose_name = "Health Package Pricing"
        verbose_name_plural = "Health Packages Pricing"
        unique_together = [['health_package', 'hospital'], ]

    def __str__(self):
        return self.health_package.code

    def save(self, *args, **kwargs):
        super(HealthPackagePricing, self).save(*args, **kwargs)
