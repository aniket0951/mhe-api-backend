# Generated by Django 3.0.2 on 2020-01-17 12:05

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('master_data', '0001_initial'),
        ('health_tests', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='HealthPackage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField()),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('billing_group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='master_data.BillingGroup')),
                ('included_health_tests', models.ManyToManyField(to='health_tests.HealthTest')),
            ],
            options={
                'verbose_name': 'Health Package',
                'verbose_name_plural': 'Health Packages',
            },
        ),
        migrations.CreateModel(
            name='HealthPackagePricing',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('price', models.IntegerField()),
                ('health_package', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='health_packages.HealthPackage')),
                ('hospital', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='master_data.Hospital')),
            ],
            options={
                'verbose_name': 'Health Package Pricing',
                'verbose_name_plural': 'Health Packages Pricing',
            },
        ),
    ]
