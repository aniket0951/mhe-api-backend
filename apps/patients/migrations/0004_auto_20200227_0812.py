# Generated by Django 3.0.3 on 2020-02-27 08:12

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0003_auto_20200227_0542'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='familymember',
            unique_together=set(),
        ),
        migrations.CreateModel(
            name='PatientValidateUHID',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('uhid_number', models.CharField(max_length=20)),
                ('patient_info', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='patients.Patient')),
            ],
            options={
                'verbose_name': 'Patient Validate UHID',
                'verbose_name_plural': 'PatientValidateUHID',
            },
        ),
    ]
