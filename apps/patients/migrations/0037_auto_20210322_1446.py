# Generated by Django 3.0.3 on 2021-03-22 14:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0036_covidvaccinationregistration_vaccination_slot'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='covidvaccinationregistration',
            name='dob',
        ),
        migrations.RemoveField(
            model_name='covidvaccinationregistration',
            name='mobile_number',
        ),
        migrations.RemoveField(
            model_name='covidvaccinationregistration',
            name='name',
        ),
    ]
