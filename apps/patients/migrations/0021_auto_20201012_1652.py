# Generated by Django 3.0.3 on 2020-10-12 16:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('master_data', '0008_company'),
        ('patients', '0020_auto_20200728_2254'),
    ]

    operations = [
        migrations.AddField(
            model_name='patient',
            name='active_view',
            field=models.CharField(default='Normal', max_length=20),
        ),
        migrations.AddField(
            model_name='patient',
            name='company_info',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='patient_company_info', to='master_data.Company'),
        ),
        migrations.AddField(
            model_name='patient',
            name='corporate_email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='patient',
            name='corporate_email_otp',
            field=models.CharField(blank=True, max_length=4, null=True),
        ),
        migrations.AddField(
            model_name='patient',
            name='corporate_email_otp_expiration_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Corporatse Email OTP Key Expiration DateTime'),
        ),
    ]
