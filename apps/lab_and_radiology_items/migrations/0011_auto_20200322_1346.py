# Generated by Django 3.0.3 on 2020-03-22 13:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lab_and_radiology_items', '0010_auto_20200322_1333'),
    ]

    operations = [
        migrations.AlterField(
            model_name='homecollectionappointment',
            name='home_collections',
            field=models.ManyToManyField(blank=True, to='lab_and_radiology_items.LabRadiologyItem'),
        ),
    ]
