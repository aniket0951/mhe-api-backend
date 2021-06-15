# Generated by Django 3.0.3 on 2021-06-15 13:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0044_auto_20210520_1203'),
    ]

    operations = [
        migrations.AddField(
            model_name='patient',
            name='drive_corporate_email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='patient',
            name='drive_corporate_email_otp',
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
        migrations.AddField(
            model_name='patient',
            name='drive_corporate_email_otp_expiration_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Drive Corporate Email OTP Key Expiration DateTime'),
        ),
        migrations.AlterField(
            model_name='patient',
            name='corporate_email_otp_expiration_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Corporate Email OTP Key Expiration DateTime'),
        ),
    ]
