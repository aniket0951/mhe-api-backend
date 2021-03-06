# Generated by Django 3.0.3 on 2021-06-11 15:59

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('additional_features', '0005_auto_20210611_1238'),
    ]

    operations = [
        migrations.AddField(
            model_name='staticinstructions',
            name='title',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='drive',
            name='booking_end_time',
            field=models.DateTimeField(default=datetime.datetime(2021, 6, 11, 15, 59, 51, 63634)),
        ),
        migrations.AlterField(
            model_name='drive',
            name='booking_start_time',
            field=models.DateTimeField(default=datetime.datetime(2021, 6, 11, 15, 59, 51, 63567)),
        ),
    ]
