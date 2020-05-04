import os

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models

from apps.meta_app.models import MyBaseModel
from apps.patients.models import FamilyMember, Patient
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
                                            settings.VALID_FILE_EXTENSIONS), validate_file_size,
                                            validate_file_authenticity],
                                blank=False,
                                null=False)

    patient_info = models.ForeignKey(Patient,
                                     on_delete=models.PROTECT,
                                     null=False,
                                     blank=False,
                                     related_name='patient_documents')

    family_member = models.ForeignKey(FamilyMember,
                                      on_delete=models.PROTECT,
                                      related_name='family_personal_documents',
                                      blank=True,
                                      null=True)

    @property
    def representation(self):
        return 'Patient: {}, Document: {}'.format(self.patient_info.first_name, self.name)

    class Meta:
        verbose_name = "Patient Personal Document"
        verbose_name_plural = "Patient Personal Documents"

    def __str__(self):
        return self.representation
