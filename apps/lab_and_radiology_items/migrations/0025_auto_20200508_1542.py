# Generated by Django 3.0.6 on 2020-05-08 15:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lab_and_radiology_items', '0024_auto_20200506_0119'),
    ]

    operations = [
        migrations.AlterField(
            model_name='homecollectionappointment',
            name='appointment_date',
            field=models.DateField(),
        ),
    ]
