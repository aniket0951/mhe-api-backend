from django.db import models

from apps.patients.models import Patient
from django_extensions.db.models import TimeStampedModel


# Create your models here.
class MobileDevice(models.Model):
    participant = models.OneToOneField(
        Patient, related_name='device', on_delete=models.PROTECT)
    platform = models.CharField(max_length=20, choices=(
        ('iOS', 'iOS'), ('Android', 'Android'),))
    version = models.CharField(max_length=10, blank=True, null=True)
    token = models.TextField()
    device_id = models.TextField(blank=True, null=True)


class MobileNotification(TimeStampedModel):
    recipient = models.ForeignKey(
        Patient, related_name='user_device_notifications', on_delete=models.PROTECT)
    title = models.CharField(max_length=512, null=True, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=10, default='unread')
