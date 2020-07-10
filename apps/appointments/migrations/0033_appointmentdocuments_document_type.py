# Generated by Django 3.0.3 on 2020-06-23 19:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0032_appointment_patient_ready'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointmentdocuments',
            name='document_type',
            field=models.CharField(choices=[('Prescription', 'Prescription'), ('Lab', 'Lab'), ('Radiology', 'Radiology')], default='Prescription', max_length=15),
        ),
    ]