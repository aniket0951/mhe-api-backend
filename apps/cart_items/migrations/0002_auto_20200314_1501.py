# Generated by Django 3.0.3 on 2020-03-14 15:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('master_data', '0003_homecareservice'),
        ('cart_items', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='healthpackagecart',
            name='hospital',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='master_data.Hospital'),
        ),
    ]
