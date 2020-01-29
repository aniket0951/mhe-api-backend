# Generated by Django 3.0.2 on 2020-01-17 12:05

import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserTypes',
            fields=[
                ('group_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='auth.Group')),
                ('slug', models.SlugField(blank=True, null=True, unique=True)),
                ('description', models.CharField(max_length=200)),
            ],
            options={
                'verbose_name': 'User Type',
                'verbose_name_plural': 'Users Types',
            },
            bases=('auth.group',),
            managers=[
                ('objects', django.contrib.auth.models.GroupManager()),
            ],
        ),
    ]
