# Generated by Django 3.0.3 on 2020-04-08 10:53

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('patients', '0016_patient_new_mobile_verification_otp'),
    ]

    operations = [
        migrations.CreateModel(
            name='MobileNotification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('title', models.CharField(blank=True, max_length=512, null=True)),
                ('message', models.TextField()),
                ('status', models.CharField(default='unread', max_length=10)),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='user_device_notifications', to='patients.Patient')),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MobileDevice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform', models.CharField(choices=[('iOS', 'iOS'), ('Android', 'Android')], max_length=20)),
                ('token', models.TextField()),
                ('participant', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='device', to='patients.Patient')),
            ],
        ),
    ]
