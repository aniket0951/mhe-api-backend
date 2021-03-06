# Generated by Django 3.0.3 on 2021-10-25 17:26

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('phlebo', '0002_auto_20211013_1746'),
        ('home_care', '0002_auto_20211011_1503'),
    ]

    operations = [
        migrations.CreateModel(
            name='LabTestAppointmentHistory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('appointment_status', models.CharField(max_length=50)),
                ('phlebo_status', models.CharField(max_length=50)),
                ('appointment', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='home_care.LabTestAppointment')),
                ('phlebo', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='phlebo.Phlebo')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
