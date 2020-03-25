# Generated by Django 3.0.3 on 2020-03-25 06:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('master_data', '0004_hospital_is_home_collection_supported'),
    ]

    operations = [
        migrations.AddField(
            model_name='hospital',
            name='health_package_department_code',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='hospital',
            name='health_package_doctor_code',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='hospital',
            name='is_health_package_online_purchase_supported',
            field=models.BooleanField(default=False),
        ),
    ]
