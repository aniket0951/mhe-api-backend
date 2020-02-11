from django.db import models

from apps.health_tests.models import HealthTest
from apps.master_data.models import BillingGroup, Hospital
from apps.meta_app.models import MyBaseModel

# Create your models here.


class HealthPackage(MyBaseModel):

    name = models.CharField(max_length=50,
                            null=False,
                            blank=False,
                            )

    description = models.TextField()

    included_health_tests = models.ManyToManyField(HealthTest)

    billing_group = models.ForeignKey(
        BillingGroup,
        on_delete=models.PROTECT,
        null=False,
        blank=False)

    start_date = models.DateField()

    end_date = models.DateField()

    class Meta:
        verbose_name = "Health Package"
        verbose_name_plural = "Health Packages"

    def __str__(self):
        return self.name

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

    class Meta:
        verbose_name = "Health Package Pricing"
        verbose_name_plural = "Health Packages Pricing"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super(HealthPackagePricing, self).save(*args, **kwargs)
