# Generated by Django 3.0.3 on 2021-02-18 12:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manipal_admin', '0008_auto_20210216_1400'),
    ]

    operations = [
        migrations.AlterField(
            model_name='manipaladmin',
            name='menus',
            field=models.ManyToManyField(null=True, to='manipal_admin.AdminMenu'),
        ),
    ]