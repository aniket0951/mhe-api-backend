# Generated by Django 3.0.3 on 2021-03-05 11:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doctors', '0012_doctorcharges'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctor',
            name='talks_publications',
            field=models.TextField(blank=True, null=True),
        ),
    ]
