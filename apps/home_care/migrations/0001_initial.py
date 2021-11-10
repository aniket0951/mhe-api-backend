# Generated by Django 3.0.3 on 2021-10-11 15:03

import apps.home_care.models
import django.contrib.postgres.fields.jsonb
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django_clamd.validators
import utils.custom_storage
import utils.validators
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('master_data', '0040_helplinenumbers_title'),
    ]

    operations = [
        migrations.CreateModel(
            name='HealthTest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.SlugField(blank=True, max_length=200, null=True, unique=True)),
                ('description', models.CharField(max_length=300)),
            ],
            options={
                'verbose_name': 'Home Care',
                'verbose_name_plural': 'Home Care',
            },
        ),
        migrations.CreateModel(
            name='HealthTestCartItems',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='HealthTestCategory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.SlugField(blank=True, max_length=200, null=True, unique=True)),
                ('name', models.CharField(max_length=200)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='HealthTestPricing',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('price', models.IntegerField()),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Health Test Pricing',
                'verbose_name_plural': 'Health Test Pricing',
            },
        ),
        migrations.CreateModel(
            name='HospitalRegion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('pin', models.CharField(max_length=20)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LabTestAppointment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('health_tests_origin', django.contrib.postgres.fields.jsonb.JSONField()),
                ('order_id', models.CharField(max_length=50, unique=True)),
                ('distance', models.FloatField()),
                ('other_reason', models.TextField(blank=True, null=True)),
                ('appointment_date', models.DateTimeField()),
                ('appointment_identifier', models.CharField(blank=True, max_length=50, null=True)),
                ('appointment_status', models.CharField(max_length=15)),
                ('phlebo_status', models.CharField(max_length=15)),
                ('prescription', models.FileField(storage=utils.custom_storage.FileStorage(), upload_to=apps.home_care.models.generate_prescription_file_path, validators=[django.core.validators.FileExtensionValidator(['doc', 'docx', 'xml', 'dotx', 'pdf', 'txt', 'xls', 'xlsx', 'csv', 'ppt', 'pps', 'ppsx', 'bmp', 'jpg', 'jpeg', 'pjpeg', 'gif', 'png', 'svg', 'html']), utils.validators.validate_file_size, utils.validators.validate_file_authenticity, django_clamd.validators.validate_file_infection])),
                ('booked_via_app', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LabTestSlotsMaster',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('slot_from', models.TimeField()),
                ('slot_to', models.TimeField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LabTestSlotsWeeklyMaster',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('day', models.CharField(max_length=20)),
                ('hospital', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='master_data.Hospital')),
                ('slot', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='home_care.LabTestSlotsMaster')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LabTestSlotSchedule',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('pin', models.CharField(max_length=20)),
                ('hospital', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='master_data.Hospital')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
