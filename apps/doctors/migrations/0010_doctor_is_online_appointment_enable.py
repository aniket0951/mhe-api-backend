# Generated by Django 3.0.3 on 2020-07-17 23:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doctors', '0009_auto_20200714_0103'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctor',
            name='is_online_appointment_enable',
            field=models.BooleanField(default=True),
        ),
    ]
