# Generated by Django 3.0.3 on 2020-03-19 17:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0008_appointment_payment_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='app_booked',
            field=models.BooleanField(default=True),
        ),
    ]