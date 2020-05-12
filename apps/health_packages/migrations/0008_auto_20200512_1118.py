# Generated by Django 3.0.6 on 2020-05-12 11:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('health_packages', '0007_healthpackage_is_popular'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='healthpackage',
            name='age_group',
        ),
        migrations.AddField(
            model_name='healthpackage',
            name='age_from',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='healthpackage',
            name='age_to',
            field=models.IntegerField(default=120),
        ),
    ]
