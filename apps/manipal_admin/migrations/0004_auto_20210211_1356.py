# Generated by Django 3.0.3 on 2021-02-11 13:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('manipal_admin', '0003_auto_20210211_1348'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adminmenu',
            name='parent_menu',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manipal_admin.AdminMenu'),
        ),
    ]
