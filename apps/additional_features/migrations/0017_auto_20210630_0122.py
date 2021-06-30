# Generated by Django 3.0.3 on 2021-06-30 01:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('additional_features', '0016_remove_driveinventory_dose'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='drivebooking',
            name='dose',
        ),
        migrations.AddField(
            model_name='driveinventory',
            name='dose',
            field=models.CharField(default='dose', max_length=8),
        ),
    ]