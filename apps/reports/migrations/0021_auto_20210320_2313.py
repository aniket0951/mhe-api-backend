# Generated by Django 3.0.3 on 2021-03-20 23:13

import apps.reports.models
import django.core.validators
from django.db import migrations, models
import django_clamd.validators
import utils.custom_storage
import utils.validators


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0020_visitreport_patient_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reportdocuments',
            name='lab_report',
            field=models.FileField(blank=True, null=True, storage=utils.custom_storage.FileStorage(), upload_to=apps.reports.models.generate_lab_report_file_path, validators=[django.core.validators.FileExtensionValidator(['doc', 'docx', 'xml', 'dotx', 'pdf', 'txt', 'xls', 'xlsx', 'csv', 'ppt', 'pps', 'ppsx', 'bmp', 'jpg', 'jpeg', 'pjpeg', 'gif', 'png', 'svg', 'html']), utils.validators.validate_file_size, utils.validators.validate_file_authenticity, django_clamd.validators.validate_file_infection]),
        ),
        migrations.AlterField(
            model_name='reportdocuments',
            name='radiology_report',
            field=models.FileField(blank=True, null=True, storage=utils.custom_storage.FileStorage(), upload_to=apps.reports.models.generate_radiology_report_file_path, validators=[django.core.validators.FileExtensionValidator(['doc', 'docx', 'xml', 'dotx', 'pdf', 'txt', 'xls', 'xlsx', 'csv', 'ppt', 'pps', 'ppsx', 'bmp', 'jpg', 'jpeg', 'pjpeg', 'gif', 'png', 'svg', 'html']), utils.validators.validate_file_size, utils.validators.validate_file_authenticity, django_clamd.validators.validate_file_infection]),
        ),
    ]
