# Generated by Django 3.0.3 on 2020-06-23 19:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0033_appointmentdocuments_document_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='appointmentdocuments',
            name='description',
        ),
    ]
