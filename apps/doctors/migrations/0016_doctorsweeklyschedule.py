# Generated by Django 3.0.3 on 2021-08-13 09:36

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('master_data', '0040_helplinenumbers_title'),
        ('doctors', '0015_doctor_service'),
    ]

    operations = [
        migrations.CreateModel(
            name='DoctorsWeeklySchedule',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('day', models.CharField(blank=True, choices=[('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'), ('Thursday', 'Thursday'), ('Friday', 'Friday'), ('Saturday', 'Saturday'), ('Sunday', 'Sunday')], max_length=30, null=True)),
                ('from_time', models.TimeField(blank=True, null=True)),
                ('to_time', models.TimeField(blank=True, null=True)),
                ('department', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.PROTECT, related_name='doctor_department_weekly_schedule', to='master_data.Department')),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='doctors.Doctor')),
                ('hospital', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='doctor_hospital_weekly_schedule', to='master_data.Hospital')),
            ],
            options={
                'verbose_name': 'Consultation Charges',
                'verbose_name_plural': 'Consultation charges',
            },
        ),
    ]
