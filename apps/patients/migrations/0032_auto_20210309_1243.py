# Generated by Django 3.0.3 on 2021-03-09 12:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0031_auto_20210309_1228'),
    ]

    operations = [
        migrations.AlterField(
            model_name='covidvaccinationregistration',
            name='registration_no',
            field=models.AutoField(default=100000, editable=False, primary_key=True, serialize=False),
        ),
    ]
