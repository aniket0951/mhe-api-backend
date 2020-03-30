from django.db import models

from apps.doctors.models import Doctor
from apps.meta_app.models import MyBaseModel


class Report(MyBaseModel):

    uhid = models.CharField(max_length=20,
                            blank=False,
                            null=False)

    code = models.CharField(max_length=100,
                            blank=False,
                            null=False)

    name = models.CharField(max_length=500,
                            blank=False,
                            null=False)

    doctor_name = models.CharField(max_length=500,
                                   null=True,
                                   blank=True)

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.PROTECT,
        null=True,
        blank=True)

    time = models.DateTimeField()

    class Meta:
        verbose_name = "Report"
        verbose_name_plural = "Reports"

    def __str__(self):
        return self.name


class NumericReportDetails(MyBaseModel):

    identifier = models.CharField(max_length=20,
                                  blank=False,
                                  null=False)

    name = models.CharField(max_length=100,
                            blank=False,
                            null=False)

    observation_value = models.CharField(max_length=100,
                                         blank=False,
                                         null=False)

    observation_range = models.CharField(max_length=100,
                                         blank=False,
                                         null=False)

    report = models.ForeignKey(
        Report,
        on_delete=models.PROTECT,
        related_name='numeric_report',
        null=True,
        blank=True)

    class Meta:
        verbose_name = "Numeric Report Detail"
        verbose_name_plural = "Numeric Report Details"

    def __str__(self):
        return self.name


class StringReportDetails(MyBaseModel):

    code = models.CharField(max_length=20,
                            blank=False,
                            null=False)

    name = models.CharField(max_length=100,
                            blank=False,
                            null=False)

    observation_value = models.CharField(max_length=100,
                                         blank=False,
                                         null=False)
    report = models.ForeignKey(
        Report,
        on_delete=models.PROTECT,
        null=True,
        blank=True)

    class Meta:
        verbose_name = "String Report Detail"
        verbose_name_plural = "String Report Details"

    def __str__(self):
        return self.name


class TextReportDetails(MyBaseModel):

    code = models.CharField(max_length=20,
                            blank=False,
                            null=False)

    name = models.CharField(max_length=100,
                            blank=False,
                            null=False)

    observation_value = models.TextField(max_length=10000000,
                                         blank=False,
                                         null=False)
    report = models.ForeignKey(
        Report,
        on_delete=models.PROTECT,
        null=True,
        blank=True)

    class Meta:
        verbose_name = "Text Report Detail"
        verbose_name_plural = "Text Report Details"

    def __str__(self):
        return self.name
