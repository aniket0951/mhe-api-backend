from django.db import models

from apps.health_tests.models import HealthTest
from apps.master_data.models import BillingGroup, BillingSubGroup, Hospital
from apps.meta_app.models import MyBaseModel

# Create your models here.


class HealthPackage(MyBaseModel):

    code = models.SlugField(unique=True,
                            blank=True,
                            null=True)

    name = models.CharField(max_length=200,
                            null=False,
                            blank=False,
                            )

    included_health_tests = models.ManyToManyField(HealthTest,
                                                   related_name='health_package'
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
        on_delete=models.PROTECT,
        null=False,
        blank=False)

    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.PROTECT,
        null=False,
        blank=False)

    price = models.IntegerField()

    start_date = models.DateField()

    end_date = models.DateField(null=True,
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
