# Generated by Django 3.0.3 on 2021-06-30 01:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('additional_features', '0015_auto_20210618_1559'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='driveinventory',
            name='dose',
        ),
    ]