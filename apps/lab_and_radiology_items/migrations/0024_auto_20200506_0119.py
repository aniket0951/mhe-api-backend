# Generated by Django 3.0.3 on 2020-05-06 01:19

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0019_auto_20200418_0741'),
        ('lab_and_radiology_items', '0023_auto_20200506_0117'),
    ]

    operations = [
        migrations.AddField(
            model_name='homecollectionappointment',
            name='address',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='homecollectionappointment',
            name='referenced_address',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='patient_home_collection_appointment', to='patients.PatientAddress'),
        ),
        migrations.AddField(
            model_name='patientserviceappointment',
            name='address',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='patientserviceappointment',
            name='referenced_address',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='patient_service_appointment', to='patients.PatientAddress'),
        ),
    ]