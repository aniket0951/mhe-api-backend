# Generated by Django 3.0.3 on 2021-04-05 11:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doctors', '0013_doctor_talks_publications'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctorcharges',
            name='plan_code',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
