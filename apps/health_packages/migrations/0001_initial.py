# Generated by Django 3.0.3 on 2020-02-18 11:46

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
                ('code', models.SlugField(blank=True, null=True, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('included_health_tests', models.ManyToManyField(related_name='health_package', to='health_tests.HealthTest')),
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
                ('start_date', models.DateField()),
                ('end_date', models.DateField(blank=True, null=True)),
                ('health_package', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='health_packages.HealthPackage')),
                ('hospital', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='master_data.Hospital')),
            ],
            options={
                'verbose_name': 'Health Package Pricing',
                'verbose_name_plural': 'Health Packages Pricing',
                'unique_together': {('health_package', 'hospital')},
            },
        ),
    ]
