from django.db import models

from apps.master_data.models import BillingGroup, BillingSubGroup, Hospital
from apps.meta_app.models import MyBaseModel

# Create your models here.


class HealthTest(MyBaseModel):

    name = models.CharField(max_length=50,
                            null=False,
                            blank=False,
                            )

    description = models.TextField()

    remarks = models.TextField()

    code = models.SlugField(unique=True,
                            blank=True,
                            null=True)

    billing_group = models.ForeignKey(
        BillingGroup,
        on_delete=models.PROTECT,
        null=False,
        blank=False)

    billing_sub_group = models.ForeignKey(
        BillingSubGroup,
        on_delete=models.PROTECT,
        null=False,
        blank=False)

    class Meta:
        verbose_name = "Health Test"
        verbose_name_plural = "Health Tests"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super(HealthTest, self).save(*args, **kwargs)


class HealthTestPricing(MyBaseModel):

    health_test = models.ForeignKey(
        HealthTest,
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
        verbose_name = "Health Test Pricing"
        verbose_name_plural = "Health Test Pricing"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super(HealthTestPricing, self).save(*args, **kwargs)
