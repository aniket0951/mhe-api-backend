# Generated by Django 3.0.3 on 2020-03-18 09:51

import apps.dashboard.models
import django.core.validators
from django.db import migrations, models
import utils.custom_storage
import utils.validators


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dashboardbanner',
            name='banner_type',
            field=models.CharField(choices=[('HomeCollection', 'HomeCollection')], default='HomeCollection', max_length=14, verbose_name='Banner Type'),
        ),
        migrations.AlterField(
            model_name='dashboardbanner',
            name='image',
            field=models.ImageField(default=None, storage=utils.custom_storage.MediaStorage(), upload_to=apps.dashboard.models.generate_banner_picture_path, validators=[django.core.validators.FileExtensionValidator(['jpg', 'jpeg', 'pjpeg', 'png', 'svg']), utils.validators.validate_file_size, utils.validators.validate_file_authenticity], verbose_name='Display Picture'),
            preserve_default=False,
        ),
    ]
