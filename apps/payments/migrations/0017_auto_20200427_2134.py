# Generated by Django 3.0.3 on 2020-04-27 21:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0016_auto_20200404_1713'),
    ]

    operations = [
        migrations.RenameField(
            model_name='payment',
            old_name='bank_ref_num',
            new_name='receipt_number',
        ),
        migrations.AlterField(
            model_name='payment',
            name='settled_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
