# Generated by Django 3.0.3 on 2020-06-18 13:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0028_appointment_appointment_mode'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='enable_join_button',
            field=models.BooleanField(default=False),
        ),
    ]
