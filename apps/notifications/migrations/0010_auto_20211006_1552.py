# Generated by Django 3.0.3 on 2021-10-06 15:52

import apps.notifications.models
import django.core.validators
from django.db import migrations, models
import django_clamd.validators
import utils.custom_storage
import utils.validators


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0009_auto_20211006_1514'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schedulenotifications',
            name='file',
            field=models.FileField(blank=True, null=True, storage=utils.custom_storage.FileStorage(), upload_to=apps.notifications.models.generate_notification_uhids_file_path, validators=[django.core.validators.FileExtensionValidator(['doc', 'docx', 'xml', 'dotx', 'pdf', 'txt', 'xls', 'xlsx', 'csv', 'ppt', 'pps', 'ppsx', 'bmp', 'jpg', 'jpeg', 'pjpeg', 'gif', 'png', 'svg', 'html']), utils.validators.validate_file_size, utils.validators.validate_file_authenticity, django_clamd.validators.validate_file_infection]),
        ),
    ]
