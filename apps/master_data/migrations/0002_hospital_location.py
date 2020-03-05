# Generated by Django 3.0.3 on 2020-03-05 06:37

import django.contrib.gis.db.models.fields
import django.contrib.gis.geos.point
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('master_data', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='hospital',
            name='location',
            field=django.contrib.gis.db.models.fields.PointField(blank=True, default=django.contrib.gis.geos.point.Point(1, 1), null=True, srid=4326),
        ),
    ]
