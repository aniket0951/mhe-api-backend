# Generated by Django 3.0.3 on 2020-03-27 13:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0014_familymember_new_mobile'),
        ('lab_and_radiology_items', '0017_auto_20200326_1811'),
    ]

    operations = [
        migrations.AlterField(
            model_name='homecollectionappointment',
            name='family_member',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='family_home_collection_appointment', to='patients.FamilyMember'),
        ),
        migrations.AlterField(
            model_name='patientserviceappointment',
            name='family_member',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='family_service_appointment', to='patients.FamilyMember'),
        ),
        migrations.AlterField(
            model_name='uploadprescription',
            name='family_member',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='family_prescription', to='patients.FamilyMember'),
        ),
    ]
