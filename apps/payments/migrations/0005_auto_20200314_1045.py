# Generated by Django 3.0.3 on 2020-03-14 10:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0004_auto_20200314_1043'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='bank_ref_num',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]