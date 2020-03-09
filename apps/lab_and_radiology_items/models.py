from django.db import models

from apps.master_data.models import BillingGroup, BillingSubGroup, Hospital
from apps.meta_app.models import MyBaseModel



class LabRadiologyItem(MyBaseModel):

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
        verbose_name = "LabRadiology Item"
        verbose_name_plural = "LabRadiology Items"

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        super(LabRadiologyItem, self).save(*args, **kwargs)


class LabRadiologyItemPricing(MyBaseModel):

    item = models.ForeignKey(LabRadiologyItem,
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
        unique_together = [['item', 'hospital'], ]

    def __str__(self):
        return self.item.code

    def save(self, *args, **kwargs):
        super(LabRadiologyItemPricing, self).save(*args, **kwargs)
