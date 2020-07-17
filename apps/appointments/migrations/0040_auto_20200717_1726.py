# Generated by Django 3.0.3 on 2020-07-17 17:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0039_auto_20200716_1512'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='episode_date_time',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='appointment',
            name='episode_number',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='prescriptiondocuments',
            name='appointment_identifier',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='prescriptiondocuments',
            name='department_code',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='prescriptiondocuments',
            name='episode_date_time',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='prescriptiondocuments',
            name='episode_number',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='prescriptiondocuments',
            name='file_type',
            field=models.CharField(default='Prescription', max_length=50),
        ),
        migrations.AddField(
            model_name='prescriptiondocuments',
            name='hospital_code',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
