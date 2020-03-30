# Generated by Django 3.0.3 on 2020-03-29 07:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0012_auto_20200327_1317'),
    ]

    operations = [
        migrations.RenameField(
            model_name='payment',
            old_name='uhid_family_member',
            new_name='payment_done_for_family_member',
        ),
        migrations.RenameField(
            model_name='payment',
            old_name='uhid_patient',
            new_name='payment_done_for_patient',
        ),
        migrations.AddField(
            model_name='payment',
            name='episode_number',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='payment_for_health_package',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='payment',
            name='payment_for_ip_deposit',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='payment',
            name='payment_for_op_billing',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='payment',
            name='payment_for_uhid_creation',
            field=models.BooleanField(default=False),
        ),
    ]
