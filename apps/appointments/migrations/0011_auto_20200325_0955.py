# Generated by Django 3.0.3 on 2020-03-25 09:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0010_healthpackageappointment'),
    ]

    operations = [
        migrations.RenameField(
            model_name='appointment',
            old_name='app_booked',
            new_name='booked_via_app',
        ),
        migrations.RenameField(
            model_name='healthpackageappointment',
            old_name='app_booked',
            new_name='booked_via_app',
        ),
    ]
