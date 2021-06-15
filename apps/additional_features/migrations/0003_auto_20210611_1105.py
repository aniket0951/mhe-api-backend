# Generated by Django 3.0.3 on 2021-06-11 11:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('master_data', '0035_auto_20210611_1105'),
        ('additional_features', '0002_drive_drivebilling_drivebooking_driveinventory'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='drive',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='drive',
            name='updated_by',
        ),
        migrations.RemoveField(
            model_name='drivebilling',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='drivebilling',
            name='updated_by',
        ),
        migrations.RemoveField(
            model_name='drivebooking',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='drivebooking',
            name='updated_by',
        ),
        migrations.RemoveField(
            model_name='driveinventory',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='driveinventory',
            name='updated_by',
        ),
        migrations.AlterField(
            model_name='drive',
            name='date',
            field=models.DateField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='drive',
            name='type',
            field=models.CharField(choices=[('apartment', 'Apartment'), ('corporate', 'Corporate')], max_length=100),
        ),
        migrations.AlterField(
            model_name='drivebooking',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('booked', 'Booked'), ('cancelled', 'Cancelled')], default='pending', max_length=15),
        ),
        migrations.AlterField(
            model_name='driveinventory',
            name='dose',
            field=models.CharField(max_length=8),
        ),
        migrations.AlterField(
            model_name='driveinventory',
            name='item_quantity',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='driveinventory',
            name='medicine',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='medicine_name', to='master_data.Medicine'),
        ),
    ]