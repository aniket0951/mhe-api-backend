# Generated by Django 3.0.3 on 2021-05-25 15:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0010_auto_20210525_1539'),
    ]

    operations = [
        migrations.AlterField(
            model_name='flyerscheduler',
            name='frequency',
            field=models.IntegerField(choices=[(1, 'Once-a-Day'), (0, 'EveryTime')], default=0),
        ),
    ]
