# Generated by Django 3.0.3 on 2021-03-23 11:01

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0038_auto_20210323_1045'),
    ]

    operations = [
        migrations.AlterField(
            model_name='familymember',
            name='aadhar_number',
            field=models.BigIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(100000000000), django.core.validators.MaxValueValidator(999999999999)]),
        ),
        migrations.AlterField(
            model_name='patient',
            name='aadhar_number',
            field=models.BigIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(100000000000), django.core.validators.MaxValueValidator(999999999999)]),
        ),
    ]
