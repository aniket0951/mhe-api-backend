# Generated by Django 3.0.6 on 2020-05-12 11:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('health_packages', '0008_auto_20200512_1118'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='healthpackage',
            name='gender',
        ),
    ]
