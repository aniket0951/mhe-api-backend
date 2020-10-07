import os

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models

from apps.doctors.models import Doctor
from apps.master_data.models import Hospital
from apps.meta_app.models import MyBaseModel
from utils.custom_storage import FileStorage
from utils.validators import validate_file_authenticity, validate_file_size


def generate_lab_report_file_path(self, filename):
    _, obj_file_extension = os.path.splitext(filename)
    obj_name = str(self.id) + str(obj_file_extension)
    return "reports/{0}/documents/{1}".format(self.id, obj_name)


def generate_radiology_report_file_path(self, filename):
    _, obj_file_extension = os.path.splitext(filename)
    obj_name = str(self.id) + str(obj_file_extension)
    return "reports/{0}/documents/{1}".format(self.id, obj_name)


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

    patient_name = models.CharField(max_length=500,
                                    null=True,
                                    blank=True)

    visit_id = models.CharField(max_length=100,
                                null=False,
                                blank=False)

    place_order = models.CharField(max_length=100,
                                   blank=True,
                                   null=True)

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

    visit_date_time = models.DateTimeField()

    report_type = models.CharField(max_length=20,
                                   default="Lab")

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


class ReportDocuments(MyBaseModel):

    uhid = models.CharField(max_length=20,
                            blank=False,
                            null=False)

    lab_report = models.FileField(upload_to=generate_lab_report_file_path,
                                  storage=FileStorage(),
                                  validators=[FileExtensionValidator(
                                      settings.VALID_FILE_EXTENSIONS), validate_file_size,
                                      validate_file_authenticity],
                                  blank=True,
                                  null=True)

    radiology_report = models.FileField(upload_to=generate_radiology_report_file_path,
                                        storage=FileStorage(),
                                        validators=[FileExtensionValidator(
                                            settings.VALID_FILE_EXTENSIONS), validate_file_size,
                                            validate_file_authenticity],
                                        blank=True,
                                        null=True)

    lab_name = models.CharField(max_length=500,
                                blank=True,
                                null=True)

    radiology_name = models.CharField(max_length=500,
                                      blank=True,
                                      null=True)

    doctor_name = models.CharField(max_length=500,
                                   null=True,
                                   blank=True)

    episode_number = models.CharField(max_length=100,
                                      null=False,
                                      blank=False)

    hospital = models.ForeignKey(Hospital,
                                 on_delete=models.PROTECT,
                                 null=True,
                                 blank=True)

    upload_date_time = models.DateTimeField(null=True,
                                            blank=True)

    update_date_time = models.DateTimeField(null=True,
                                            blank=True)

    class Meta:
        verbose_name = "Report Document"
        verbose_name_plural = "Report Documents"

    def __str__(self):
        return self.name


class VisitReport(MyBaseModel):

    uhid = models.CharField(max_length=20,
                            blank=False,
                            null=False)

    visit_id = models.CharField(max_length=20,
                                blank=False,
                                null=False)

    patient_class = models.CharField(max_length=100,
                                     null=False,
                                     blank=False)

    patient_name = models.CharField(max_length=500,
                                    null=True,
                                    blank=True)

    report_info = models.ManyToManyField(Report,
                                         blank=True,
                                         related_name='report_visit')

    class Meta:
        verbose_name = "Report Visit"
        verbose_name_plural = "Report Visits"
