# Generated by Django 3.0.3 on 2021-03-23 11:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0039_auto_20210323_1101'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='covidvaccinationregistration',
            name='other_user',
        ),
    ]
