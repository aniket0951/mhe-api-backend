# Generated by Django 3.0.3 on 2020-11-11 12:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('master_data', '0012_auto_20201111_1136'),
    ]

    operations = [
        migrations.AddField(
            model_name='hospital',
            name='hospital_enabled',
            field=models.BooleanField(default=True),
        ),
    ]