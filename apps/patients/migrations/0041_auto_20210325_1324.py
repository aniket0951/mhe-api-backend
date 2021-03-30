# Generated by Django 3.0.3 on 2021-03-25 13:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0040_remove_covidvaccinationregistration_other_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='covidvaccinationregistration',
            name='dose_type',
            field=models.CharField(choices=[('1', '1'), ('2', '2')], default='1', max_length=10),
        ),
        migrations.AddField(
            model_name='familymember',
            name='dob',
            field=models.DateField(blank=True, null=True, verbose_name='Date of birth'),
        ),
        migrations.AddField(
            model_name='patient',
            name='dob',
            field=models.DateField(blank=True, null=True, verbose_name='Date of birth'),
        ),
        migrations.AlterField(
            model_name='covidvaccinationregistration',
            name='status',
            field=models.CharField(choices=[('payment_pending', 'Payment Pending'), ('requested', 'Requested'), ('scheduled', 'Scheduled'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='payment_pending', max_length=30),
        ),
    ]
