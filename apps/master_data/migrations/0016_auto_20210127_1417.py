# Generated by Django 3.0.3 on 2021-01-27 14:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('master_data', '0015_feedbackrecipients'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feedbackrecipients',
            name='hospital_code',
            field=models.SlugField(),
        ),
    ]
