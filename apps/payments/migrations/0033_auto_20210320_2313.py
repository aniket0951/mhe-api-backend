# Generated by Django 3.0.3 on 2021-03-20 23:13

import apps.payments.models
import django.core.validators
from django.db import migrations, models
import django_clamd.validators
import utils.custom_storage
import utils.validators


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0032_payment_raw_info_from_manipal_response'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymentreceipts',
            name='receipt',
            field=models.FileField(storage=utils.custom_storage.FileStorage(), upload_to=apps.payments.models.generate_receipt_file_path, validators=[django.core.validators.FileExtensionValidator(['doc', 'docx', 'xml', 'dotx', 'pdf', 'txt', 'xls', 'xlsx', 'csv', 'ppt', 'pps', 'ppsx', 'bmp', 'jpg', 'jpeg', 'pjpeg', 'gif', 'png', 'svg', 'html']), utils.validators.validate_file_size, utils.validators.validate_file_authenticity, django_clamd.validators.validate_file_infection]),
        ),
    ]
