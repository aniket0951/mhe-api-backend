# Generated by Django 3.0.3 on 2020-07-27 15:18

import apps.reports.models
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import utils.custom_storage
import utils.validators
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('master_data', '0007_homecareservice_image'),
        ('reports', '0010_numericreportdetails_observation_unit'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportDocuments',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('uhid', models.CharField(max_length=20)),
                ('lab_report', models.FileField(blank=True, null=True, storage=utils.custom_storage.FileStorage(), upload_to=apps.reports.models.generate_lab_report_file_path, validators=[django.core.validators.FileExtensionValidator(['doc', 'docx', 'xml', 'dotx', 'pdf', 'txt', 'xls', 'xlsx', 'csv', 'ppt', 'pps', 'ppsx', 'bmp', 'jpg', 'jpeg', 'pjpeg', 'gif', 'png', 'svg', 'html']), utils.validators.validate_file_size, utils.validators.validate_file_authenticity])),
                ('radiology_report', models.FileField(blank=True, null=True, storage=utils.custom_storage.FileStorage(), upload_to=apps.reports.models.generate_radiology_report_file_path, validators=[django.core.validators.FileExtensionValidator(['doc', 'docx', 'xml', 'dotx', 'pdf', 'txt', 'xls', 'xlsx', 'csv', 'ppt', 'pps', 'ppsx', 'bmp', 'jpg', 'jpeg', 'pjpeg', 'gif', 'png', 'svg', 'html']), utils.validators.validate_file_size, utils.validators.validate_file_authenticity])),
                ('lab_name', models.CharField(blank=True, max_length=500, null=True)),
                ('radiology_name', models.CharField(blank=True, max_length=500, null=True)),
                ('doctor_name', models.CharField(blank=True, max_length=500, null=True)),
                ('episode_number', models.CharField(max_length=100)),
                ('upload_date_time', models.DateTimeField(blank=True, null=True)),
                ('update_date_time', models.DateTimeField(blank=True, null=True)),
                ('hospital', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='master_data.Hospital')),
            ],
            options={
                'verbose_name': 'Report Document',
                'verbose_name_plural': 'Report Documents',
            },
        ),
    ]
