from django.db import models

from apps.master_data.models import BillingGroup, BillingSubGroup, Hospital
from apps.meta_app.models import MyBaseModel

# Create your models here.


class HealthTest(MyBaseModel):

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
        verbose_name = "Health Test"
        verbose_name_plural = "Health Tests"

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        super(HealthTest, self).save(*args, **kwargs)


class HealthTestPricing(MyBaseModel):

    health_test = models.ForeignKey(HealthTest,
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
        unique_together = [['health_test', 'hospital'], ]

    def __str__(self):
        return self.health_test.code

    def save(self, *args, **kwargs):
        super(HealthTestPricing, self).save(*args, **kwargs)
