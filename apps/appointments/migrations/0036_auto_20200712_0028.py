# Generated by Django 3.0.3 on 2020-07-12 00:28

import datetime
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0035_appointmentvital'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2020, 7, 12, 0, 28, 5, 389856)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='healthpackageappointment',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]