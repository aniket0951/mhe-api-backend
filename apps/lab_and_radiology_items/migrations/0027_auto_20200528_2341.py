# Generated by Django 3.0.3 on 2020-05-28 23:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lab_and_radiology_items', '0026_patientserviceappointment_hospital'),
    ]

    operations = [
        migrations.AddField(
            model_name='homecollectionappointment',
            name='other_reason',
            field=models.TextField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='patientserviceappointment',
            name='other_reason',
            field=models.TextField(blank=True, max_length=500, null=True),
        ),
    ]