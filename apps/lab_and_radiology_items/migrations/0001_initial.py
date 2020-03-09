# Generated by Django 3.0.3 on 2020-02-26 18:39

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('master_data', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LabRadiologyItem',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.SlugField(blank=True, max_length=200, null=True, unique=True)),
                ('description', models.CharField(max_length=300)),
                ('billing_group', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='master_data.BillingGroup')),
                ('billing_sub_group', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='master_data.BillingSubGroup')),
            ],
            options={
                'verbose_name': 'LabRadiology Item',
                'verbose_name_plural': 'LabRadiology Items',
            },
        ),
        migrations.CreateModel(
            name='LabRadiologyItemPricing',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('price', models.IntegerField()),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(blank=True, null=True)),
                ('hospital', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='master_data.Hospital')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='lab_and_radiology_items.LabRadiologyItem')),
            ],
            options={
                'verbose_name': 'Health Test Pricing',
                'verbose_name_plural': 'Health Test Pricing',
                'unique_together': {('item', 'hospital')},
            },
        ),
    ]
