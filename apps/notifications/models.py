from django.db import models
import os
import uuid
from utils.custom_storage import MediaStorage
from django.core.validators import FileExtensionValidator
from django.conf import settings
from apps.patients.models import Patient
from django_extensions.db.models import TimeStampedModel
from django_clamd.validators import validate_file_infection
from utils.validators import validate_file_authenticity, validate_file_size


def generate_birthday_picture_path(self, filename):
    _, obj_file_extension = os.path.splitext(filename)
    obj_name = str(uuid.uuid4()) + str(obj_file_extension)
    return "static/birthday/images/{0}".format(obj_name)

# Create your models here.
class MobileDevice(models.Model):
    participant = models.OneToOneField(
        Patient, related_name='device', on_delete=models.PROTECT)
    platform = models.CharField(max_length=20, choices=(
        ('iOS', 'iOS'), ('Android', 'Android'),))
    version = models.CharField(max_length=30, blank=True, null=True)
    token = models.TextField()
    device_id = models.TextField(blank=True, null=True)


class MobileNotification(TimeStampedModel):
    recipient = models.ForeignKey(
        Patient, related_name='user_device_notifications', on_delete=models.PROTECT)
    title = models.CharField(max_length=512, null=True, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=10, default='unread')
    notification_image = models.ImageField(
                        upload_to=generate_birthday_picture_path,
                        storage=MediaStorage(),
                        validators=[
                            FileExtensionValidator(settings.VALID_IMAGE_FILE_EXTENSIONS), 
                            validate_file_size,
                            validate_file_authenticity,
                            validate_file_infection
                        ],
                        blank=True,
                        null=True,
                        verbose_name='Notification Picture'
                    )
