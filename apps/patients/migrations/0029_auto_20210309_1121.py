# Generated by Django 3.0.3 on 2021-03-09 11:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0028_covidvaccinationregistration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='covidvaccinationregistration',
            name='vaccination_date',
            field=models.DateField(blank=True, null=True, verbose_name='Date of vaccination'),
        ),
    ]
