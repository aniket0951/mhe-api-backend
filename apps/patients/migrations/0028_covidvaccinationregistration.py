# Generated by Django 3.0.3 on 2021-03-09 11:01

from django.db import migrations, models
import django.db.models.deletion
import phonenumber_field.modelfields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('master_data', '0016_auto_20210127_1417'),
        ('patients', '0027_auto_20210222_1017'),
    ]

    operations = [
        migrations.CreateModel(
            name='CovidVaccinationRegistration',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('registration_no', models.PositiveIntegerField(default=100000)),
                ('name', models.CharField(max_length=200, verbose_name='Name')),
                ('mobile_number', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None, verbose_name='Mobile Number')),
                ('dob', models.DateField(verbose_name='Date of birth')),
                ('vaccination_date', models.DateField(verbose_name='Date of vaccination')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('scheduled', 'Scheduled'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='pending', max_length=15)),
                ('other_user', models.BooleanField(default=False)),
                ('remarks', models.TextField(blank=True, null=True)),
                ('family_member', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='family_member_covid_registration', to='patients.FamilyMember')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='patient_covid_registration', to='patients.Patient')),
                ('preferred_hospital', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='hospital_covid_registration', to='master_data.Hospital')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
