# Generated by Django 3.0.3 on 2021-03-16 10:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('master_data', '0019_auto_20210315_1343'),
    ]

    operations = [
        migrations.RenameField(
            model_name='company',
            old_name='components',
            new_name='component_ids',
        ),
    ]
