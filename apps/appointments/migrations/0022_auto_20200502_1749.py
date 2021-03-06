# Generated by Django 3.0.3 on 2020-05-02 17:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('master_data', '0006_ambulancecontact'),
        ('appointments', '0021_auto_20200502_1737'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appointment',
            name='department',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='hospital_department', to='master_data.Department'),
        ),
    ]
