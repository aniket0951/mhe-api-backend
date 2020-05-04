# Generated by Django 3.0.3 on 2020-04-04 17:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0016_patient_new_mobile_verification_otp'),
        ('appointments', '0013_auto_20200327_0550'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appointment',
            name='family_member',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='family_appointment', to='patients.FamilyMember'),
        ),
    ]
