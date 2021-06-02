# Generated by Django 3.0.3 on 2021-05-31 14:33

import apps.notifications.models
import django.core.validators
from django.db import migrations, models
import django_clamd.validators
import utils.custom_storage
import utils.validators


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0003_auto_20200513_0405'),
    ]

    operations = [
        migrations.AddField(
            model_name='mobilenotification',
            name='birthday_image',
            field=models.ImageField(blank=True, null=True, storage=utils.custom_storage.MediaStorage(), upload_to=apps.notifications.models.generate_birthday_picture_path, validators=[django.core.validators.FileExtensionValidator(['jpg', 'jpeg', 'pjpeg', 'png', 'svg']), utils.validators.validate_file_size, utils.validators.validate_file_authenticity, django_clamd.validators.validate_file_infection], verbose_name='Birthday Picture'),
        ),
    ]