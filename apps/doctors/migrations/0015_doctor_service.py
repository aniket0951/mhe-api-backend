# Generated by Django 3.0.3 on 2021-05-31 13:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doctors', '0014_doctorcharges_plan_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctor',
            name='service',
            field=models.CharField(blank=True, choices=[('HV', 'HV'), ('VC', 'VC'), ('HVVC', 'HVVC')], max_length=6, null=True),
        ),
    ]
