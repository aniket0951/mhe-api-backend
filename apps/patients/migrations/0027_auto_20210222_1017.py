# Generated by Django 3.0.3 on 2021-02-22 10:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0026_auto_20210212_1352'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patient',
            name='corporate_email_otp',
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
        migrations.AlterField(
            model_name='patient',
            name='email_otp',
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
    ]
