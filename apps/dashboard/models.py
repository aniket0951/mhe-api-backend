import os
import uuid

from django.conf import settings
from django.core.validators import (FileExtensionValidator, MaxValueValidator,
                                    MinValueValidator)
from django.db import models

from apps.meta_app.models import MyBaseModel
from utils.custom_storage import LocalFileStorage, MediaStorage
from utils.validators import validate_file_authenticity, validate_file_size


def generate_banner_picture_path(self, filename):
    _, obj_file_extension = os.path.splitext(filename)
    obj_name = str(uuid.uuid4()) + str(obj_file_extension)
    return "static/dashboard/banners/{0}".format(obj_name)


class DashboardBanner(MyBaseModel):

    BANNER_TYPE_CHOICES = (
        ('HomeCollection', 'HomeCollection'),
    )

    image = models.ImageField(upload_to=generate_banner_picture_path,
                              storage=MediaStorage(),
                              validators=[FileExtensionValidator(
                                  settings.VALID_IMAGE_FILE_EXTENSIONS), validate_file_size,
                                  validate_file_authenticity],
                              blank=False,
                              null=False,
                              verbose_name='Display Picture')

    banner_type = models.CharField(choices=BANNER_TYPE_CHOICES,
                                   blank=False,
                                   null=False,
                                   default='HomeCollection',
                                   max_length=14,
                                   verbose_name='Banner Type')

    @property
    def representation(self):
        return 'Banner Type: {}'\
            .format(self.banner_type)

    class Meta:
        verbose_name = "Dashboard Banner"
        verbose_name_plural = "Dashboard Banners"

    def __str__(self):
        return self.representation
