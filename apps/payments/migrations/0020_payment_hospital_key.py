# Generated by Django 3.0.3 on 2020-05-04 03:31

from django.db import migrations, models
import django.db.models.deletion
import fernet_fields.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('master_data', '0006_ambulancecontact'),
        ('payments', '0019_remove_payment_health_package'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment_hospital_key',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('mid', fernet_fields.fields.EncryptedTextField(blank=True, null=True)),
                ('secret_key', fernet_fields.fields.EncryptedTextField(blank=True, null=True)),
                ('hospital', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='master_data.Hospital')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]