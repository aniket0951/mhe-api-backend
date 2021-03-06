# Generated by Django 3.0.3 on 2021-03-26 11:25

import apps.dashboard.models
import django.core.validators
from django.db import migrations, models
import django_clamd.validators
import utils.custom_storage
import utils.validators


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0003_auto_20210325_1232'),
    ]

    operations = [
        migrations.AlterField(
            model_name='faqdata',
            name='data',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='faqdata',
            name='image',
            field=models.ImageField(blank=True, null=True, storage=utils.custom_storage.MediaStorage(), upload_to=apps.dashboard.models.generate_faq_picture_path, validators=[django.core.validators.FileExtensionValidator(['jpg', 'jpeg', 'pjpeg', 'png', 'svg']), utils.validators.validate_file_size, utils.validators.validate_file_authenticity, django_clamd.validators.validate_file_infection], verbose_name='FAQ Picture'),
        ),
        migrations.AlterField(
            model_name='faqdata',
            name='question',
            field=models.TextField(blank=True, null=True),
        ),
    ]
