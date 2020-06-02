from django.db import models

from apps.doctors.models import Doctor
from apps.master_data.models import Hospital
from apps.meta_app.models import MyBaseModel


class Report(MyBaseModel):
    PATIENT_CLASS_CHOICES = (
        ('E', 'Emergency'),
        ('O', 'Outpatient'),
        ('I', 'Inpatient'),
    )

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

    visit_id = models.CharField(max_length=100,
                                null=False,
                                blank=False)

    message_id = models.CharField(max_length=100,
                                  null=False,
                                  blank=False)

    patient_class = models.CharField(choices=PATIENT_CLASS_CHOICES,
                                     blank=False,
                                     null=False,
                                     max_length=1)

    hospital = models.ForeignKey(Hospital,
                                 on_delete=models.PROTECT,
                                 null=True,
                                 blank=True)

    doctor = models.ForeignKey(Doctor,
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
                                         blank=True,
                                         null=True)

    observation_unit = models.CharField(max_length=100,
                                        blank=True,
                                        null=True)

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
        related_name='string_report',
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
        related_name='text_report',
        null=True,
        blank=True)

    class Meta:
        verbose_name = "Text Report Detail"
        verbose_name_plural = "Text Report Details"

    def __str__(self):
        return self.name


class FreeTextReportDetails(MyBaseModel):

    code = models.CharField(max_length=20,
                            blank=False,
                            null=False)

    name = models.CharField(max_length=100,
                            blank=False,
                            null=False)

    observation_value = models.CharField(max_length=10000000,
                                         blank=False,
                                         null=False)
    report = models.ForeignKey(
        Report,
        on_delete=models.PROTECT,
        related_name='free_text_report',
        null=True,
        blank=True)

    class Meta:
        verbose_name = "Free TextReport Detail"
        verbose_name_plural = "Free TextReport Details"

    def __str__(self):
        return self.name
