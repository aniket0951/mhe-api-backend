# Generated by Django 3.0.3 on 2021-04-26 13:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0041_auto_20210325_1324'),
    ]

    operations = [
        migrations.AddField(
            model_name='familymember',
            name='is_corporate',
            field=models.BooleanField(default=False, verbose_name='is_corporate'),
        ),
    ]
