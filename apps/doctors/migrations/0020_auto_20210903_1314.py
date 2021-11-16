# Generated by Django 3.0.3 on 2021-09-03 13:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doctors', '0019_auto_20210903_1306'),
    ]

    operations = [
        migrations.AlterField(
            model_name='doctorsweeklyschedule',
            name='service',
            field=models.CharField(blank=True, choices=[('HV', 'HV'), ('VC', 'VC'), ('HVVC', 'HVVC'), ('PR', 'PR')], max_length=6, null=True),
        ),
    ]