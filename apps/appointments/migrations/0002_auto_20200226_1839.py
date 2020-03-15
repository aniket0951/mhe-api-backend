# Generated by Django 3.0.3 on 2020-02-26 18:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('doctors', '0001_initial'),
        ('appointments', '0001_initial'),
        ('master_data', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='doctor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='doctor_appointment', to='doctors.Doctor'),
        ),
        migrations.AddField(
            model_name='appointment',
            name='hospital',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='hospital_appointment', to='master_data.Hospital'),
        ),
        migrations.AddField(
            model_name='appointment',
            name='req_patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='patient_appointment', to=settings.AUTH_USER_MODEL),
        ),
    ]