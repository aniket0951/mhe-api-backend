# Generated by Django 3.0.3 on 2020-03-10 08:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('master_data', '0002_hospital_location'),
        ('health_packages', '0003_auto_20200305_0858'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='healthpackage',
            name='category',
        ),
        migrations.AddField(
            model_name='healthpackage',
            name='specialisation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='health_package', to='master_data.Specialisation'),
        ),
        migrations.DeleteModel(
            name='HealthPackageCategory',
        ),
    ]
