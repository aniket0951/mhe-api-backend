# Generated by Django 3.0.3 on 2021-02-16 14:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manipal_admin', '0007_adminmenu_parent_menu'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adminrole',
            name='menus',
            field=models.ManyToManyField(null=True, to='manipal_admin.AdminMenu'),
        ),
    ]
