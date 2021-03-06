# Generated by Django 3.0.3 on 2020-03-22 11:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('health_packages', '0006_auto_20200310_1101'),
        ('master_data', '0003_homecareservice'),
        ('payments', '0008_auto_20200321_1114'),
        ('appointments', '0009_appointment_app_booked'),
    ]

    operations = [
        migrations.CreateModel(
            name='HealthPackageAppointment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('appointment_date', models.DateField(blank=True, null=True)),
                ('appointment_slot', models.TimeField(blank=True, null=True)),
                ('appointment_identifier', models.CharField(blank=True, max_length=20, null=True)),
                ('appointment_status', models.CharField(default='Not Booked', max_length=10)),
                ('app_booked', models.BooleanField(default=True)),
                ('health_package', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='health_packages.HealthPackage')),
                ('hospital', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='hospital_health_appointment', to='master_data.Hospital')),
                ('payment', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='payments.Payment')),
                ('reason', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='cancellation_reason_health_appointment', to='appointments.CancellationReason')),
            ],
        ),
    ]
