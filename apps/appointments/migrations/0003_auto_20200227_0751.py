# Generated by Django 3.0.3 on 2020-02-27 07:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0003_auto_20200227_0542'),
        ('appointments', '0002_auto_20200226_1839'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appointment',
            name='req_patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='patient_appointment', to='patients.Patient'),
        ),
    ]
