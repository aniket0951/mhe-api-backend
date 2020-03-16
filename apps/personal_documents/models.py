import os

from django.core.validators import FileExtensionValidator
from django.db import models

from apps.meta_app.models import MyBaseModel
from apps.patients.models import Patient
from manipal_api.settings import VALID_FILE_EXTENSIONS
from utils.custom_storage import FileStorage
from utils.validators import validate_file_authenticity, validate_file_size


def generate_personal_file_path(self, filename):
    _, obj_file_extension = os.path.splitext(filename)
    obj_name = str(self.id) + str(obj_file_extension)
    return "users/{0}/documents/{1}".format(self.id, obj_name)


class PatientPersonalDocuments(MyBaseModel):

    name = models.CharField(max_length=500,
                            blank=False,
                            null=False)

    description = models.TextField(blank=True,
                                   null=True)

    document = models.FileField(upload_to=generate_personal_file_path,
                                storage=FileStorage(),
                                validators=[FileExtensionValidator(
                                            VALID_FILE_EXTENSIONS), validate_file_size,
                                            validate_file_authenticity],
                                blank=False,
                                null=False)

    patient_info = models.ForeignKey(Patient,
                                     on_delete=models.PROTECT,
                                     null=True,
                                     blank=True,
                                     related_name='patient_documents')

    @property
    def representation(self):
        return 'Patient: {}, Document: {}'.format(self.patient_info.first_name, self.name)

    class Meta:
        verbose_name = "Patient Personal Document"
        verbose_name_plural = "Patient Personal Documents"

    def __str__(self):
        return self.representation
