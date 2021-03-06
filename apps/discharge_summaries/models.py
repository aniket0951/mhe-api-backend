import os

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models

from apps.doctors.models import Doctor
from apps.master_data.models import Department, Hospital
from apps.meta_app.models import MyBaseModel
from utils.custom_storage import FileStorage
from utils.validators import validate_file_authenticity, validate_file_size
from django_clamd.validators import validate_file_infection


def generate_dischage_summary_file_path(self, filename):
    _, obj_file_extension = os.path.splitext(filename)
    obj_name = str(self.id) + str(obj_file_extension)
    return "dischage_summaries/{0}/documents/{1}".format(self.id, obj_name)


class DischargeSummary(MyBaseModel):

    uhid = models.CharField(max_length=20,
                            blank=False,
                            null=False)

    visit_id = models.CharField(max_length=20,
                            blank=True,
                            null=True)

    name = models.CharField(max_length=500,
                            blank=False,
                            null=False)

    file_name = models.CharField(max_length=500,
                            blank=True,
                            null=True)

    doctor_name = models.CharField(max_length=500,
                            blank=True,
                            null=True)

    hospital = models.ForeignKey(Hospital,
                                 on_delete=models.PROTECT,
                                 null=True,
                                 blank=True)

    doctor = models.ForeignKey(Doctor,
                               on_delete=models.PROTECT,
                               null=True,
                               blank=True)

    discharge_document = models.FileField(upload_to=generate_dischage_summary_file_path,
                                          storage=FileStorage(),
                                          validators=[
                                              FileExtensionValidator(settings.VALID_FILE_EXTENSIONS), 
                                              validate_file_size,
                                              validate_file_authenticity,
                                              validate_file_infection
                                            ],
                                          blank=False,
                                          null=False)

    time = models.DateTimeField()

    class Meta:
        verbose_name = "Discharge Summary"
        verbose_name_plural = "Discharge Summarys"

    def __str__(self):
        return self.name
