# Generated by Django 3.0.5 on 2020-04-27 13:29

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('patient_registration', '0010_province'),
    ]

    operations = [
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.SlugField(unique=True)),
                ('description', models.TextField(max_length=100)),
                ('province', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='province_city', to='patient_registration.Province')),
            ],
            options={
                'verbose_name': 'City',
                'verbose_name_plural': 'City',
            },
        ),
        migrations.CreateModel(
            name='Zipcode',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.SlugField(unique=True)),
                ('description', models.TextField(max_length=100)),
                ('city', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='city_zipcode', to='patient_registration.City')),
            ],
            options={
                'verbose_name': 'Zipcode',
                'verbose_name_plural': 'Zipcode',
            },
        ),
    ]
