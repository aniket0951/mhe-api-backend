# Generated by Django 3.0.2 on 2020-02-05 22:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('master_data', '0003_hospital_distance'),
    ]

    operations = [
        migrations.AddField(
            model_name='hospital',
            name='latitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='hospital',
            name='longitude',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
