# Generated by Django 3.0.3 on 2020-05-05 16:03

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lab_and_radiology_items', '0020_auto_20200407_1304'),
    ]

    operations = [
        migrations.AddField(
            model_name='patientserviceappointment',
            name='final_address',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
    ]