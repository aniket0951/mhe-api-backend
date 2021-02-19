# Generated by Django 3.0.3 on 2021-02-16 10:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manipal_admin', '0005_auto_20210215_1341'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='adminmenu',
            name='parent_menu',
        ),
        migrations.AlterField(
            model_name='adminmenu',
            name='name',
            field=models.CharField(default='Admin menu', max_length=200),
        ),
        migrations.AlterField(
            model_name='adminrole',
            name='name',
            field=models.CharField(default='Admin Role', max_length=200),
        ),
    ]
