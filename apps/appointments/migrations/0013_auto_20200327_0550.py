# Generated by Django 3.0.3 on 2020-03-27 05:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0014_familymember_new_mobile'),
        ('appointments', '0012_auto_20200326_1811'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appointment',
            name='family_member',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='family_appointment', to='patients.FamilyMember'),
        ),
    ]
