# Generated by Django 3.0.2 on 2020-01-14 11:34

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0002_auto_20200114_1134'),
    ]

    operations = [
        migrations.CreateModel(
            name='Patient',
            fields=[
                ('baseuser_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, to=settings.AUTH_USER_MODEL)),
                ('unique_identifier', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ],
            options={
                'verbose_name': 'Patient',
                'verbose_name_plural': 'Patients',
                'permissions': (),
            },
            bases=('users.baseuser',),
        ),
    ]
