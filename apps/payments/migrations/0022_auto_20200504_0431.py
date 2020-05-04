# Generated by Django 3.0.3 on 2020-05-04 04:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('master_data', '0006_ambulancecontact'),
        ('payments', '0021_auto_20200504_0334'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymenthospitalkey',
            name='hospital',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='payment_hospital_key_hospital', to='master_data.Hospital'),
        ),
    ]
