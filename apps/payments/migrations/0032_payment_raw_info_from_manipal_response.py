# Generated by Django 3.0.3 on 2021-01-22 16:29

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0031_payment_bill_row_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='raw_info_from_manipal_response',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
    ]