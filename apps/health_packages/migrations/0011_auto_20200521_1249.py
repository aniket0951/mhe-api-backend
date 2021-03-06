# Generated by Django 3.0.6 on 2020-05-21 12:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('health_packages', '0010_healthpackage_gender'),
    ]

    operations = [
        migrations.AddField(
            model_name='healthpackage',
            name='benefits',
            field=models.TextField(blank=True, max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name='healthpackage',
            name='description',
            field=models.TextField(blank=True, max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name='healthpackagepricing',
            name='discount_end_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='healthpackagepricing',
            name='discount_percentage',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='healthpackagepricing',
            name='discount_start_date',
            field=models.DateField(),
        ),
    ]
