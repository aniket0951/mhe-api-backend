# Generated by Django 3.0.3 on 2021-06-11 12:38

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('additional_features', '0004_auto_20210611_1237'),
    ]

    operations = [
        migrations.AlterField(
            model_name='drive',
            name='booking_end_time',
            field=models.DateTimeField(default=datetime.datetime(2021, 6, 11, 12, 38, 30, 292156)),
        ),
        migrations.AlterField(
            model_name='drive',
            name='booking_start_time',
            field=models.DateTimeField(default=datetime.datetime(2021, 6, 11, 12, 38, 30, 291927)),
        ),
    ]
