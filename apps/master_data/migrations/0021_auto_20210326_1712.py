# Generated by Django 3.0.3 on 2021-03-26 17:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('master_data', '0020_auto_20210316_1043'),
    ]

    operations = [
        migrations.AddField(
            model_name='hospitaldepartment',
            name='service',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='hospitaldepartment',
            name='sub_service',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
    ]
