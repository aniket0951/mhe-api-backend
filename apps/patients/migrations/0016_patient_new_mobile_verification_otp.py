# Generated by Django 3.0.3 on 2020-04-02 09:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0015_auto_20200402_0427'),
    ]

    operations = [
        migrations.AddField(
            model_name='patient',
            name='new_mobile_verification_otp',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
