# Generated by Django 3.0.3 on 2021-01-25 12:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0044_appointment_is_follow_up'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='plan_code',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
    ]
