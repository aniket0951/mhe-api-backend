# Generated by Django 3.0.3 on 2020-02-26 18:39

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Appointment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('appointment_date', models.DateField()),
                ('time_slot_from', models.TimeField()),
                ('appointmentIdentifier', models.IntegerField()),
                ('status', models.PositiveSmallIntegerField(choices=[(1, 'Confirmed'), (2, 'Cancelled'), (3, 'Waiting')])),
            ],
        ),
    ]
