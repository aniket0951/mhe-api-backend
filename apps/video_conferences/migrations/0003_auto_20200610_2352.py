# Generated by Django 3.0.3 on 2020-06-10 23:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0027_healthpackageappointment_other_reason'),
        ('video_conferences', '0002_videoconference_recording_link'),
    ]

    operations = [
        migrations.AddField(
            model_name='videoconference',
            name='room_sid',
            field=models.CharField(max_length=200, verbose_name='Room SID'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='videoconference',
            name='appointment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='appointment_video_conference', to='appointments.Appointment'),
        ),
    ]
