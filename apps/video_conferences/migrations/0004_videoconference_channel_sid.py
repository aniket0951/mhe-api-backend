# Generated by Django 3.0.3 on 2020-06-30 14:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('video_conferences', '0003_auto_20200610_2352'),
    ]

    operations = [
        migrations.AddField(
            model_name='videoconference',
            name='channel_sid',
            field=models.CharField(default=1, max_length=200, verbose_name='Channel SID'),
            preserve_default=False,
        ),
    ]
