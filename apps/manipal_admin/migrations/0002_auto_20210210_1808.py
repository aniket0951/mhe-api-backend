# Generated by Django 3.0.3 on 2021-02-10 18:08

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('master_data', '0016_auto_20210127_1417'),
        ('manipal_admin', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdminMenu',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('parent_menu', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manipal_admin.AdminMenu')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='manipaladmin',
            name='hospital',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='hospital_name', to='master_data.Hospital'),
        ),
        migrations.CreateModel(
            name='AdminRole',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200)),
                ('menus', models.ManyToManyField(to='manipal_admin.AdminMenu')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='manipaladmin',
            name='menus',
            field=models.ManyToManyField(to='manipal_admin.AdminMenu'),
        ),
        migrations.AddField(
            model_name='manipaladmin',
            name='role',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='manipal_admin.AdminRole'),
        ),
    ]
