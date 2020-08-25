# Generated by Django 3.0.3 on 2020-08-26 00:21

import apps.discharge_summaries.models
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import utils.custom_storage
import utils.validators
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('doctors', '0012_doctorcharges'),
        ('master_data', '0007_homecareservice_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='DischargeSummary',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('uhid', models.CharField(max_length=20)),
                ('name', models.CharField(max_length=500)),
                ('discharge_document', models.FileField(storage=utils.custom_storage.FileStorage(), upload_to=apps.discharge_summaries.models.generate_dischage_summary_file_path, validators=[django.core.validators.FileExtensionValidator(['doc', 'docx', 'xml', 'dotx', 'pdf', 'txt', 'xls', 'xlsx', 'csv', 'ppt', 'pps', 'ppsx', 'bmp', 'jpg', 'jpeg', 'pjpeg', 'gif', 'png', 'svg', 'html']), utils.validators.validate_file_size, utils.validators.validate_file_authenticity])),
                ('time', models.DateTimeField()),
                ('department', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='master_data.Department')),
                ('doctor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='doctors.Doctor')),
                ('hospital', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='master_data.Hospital')),
            ],
            options={
                'verbose_name': 'Discharge Summary',
                'verbose_name_plural': 'Discharge Summaries',
            },
        ),
    ]
