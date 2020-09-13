# Generated by Django 3.0.3 on 2020-08-27 18:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0014_auto_20200827_1825'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='report',
            name='report_visit',
        ),
        migrations.AddField(
            model_name='visitreport',
            name='report_info',
            field=models.ManyToManyField(blank=True, related_name='report_visit', to='reports.Report'),
        ),
    ]
