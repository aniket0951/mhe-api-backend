# Generated by Django 3.0.3 on 2021-09-27 16:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0055_auto_20210927_1601'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='appointment',
            name='slot_duration',
        ),
    ]
