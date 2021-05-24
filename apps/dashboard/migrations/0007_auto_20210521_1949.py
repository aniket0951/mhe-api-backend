# Generated by Django 3.0.3 on 2021-05-21 19:49

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dashboard', '0006_flyerimages'),
    ]

    operations = [
        migrations.AlterField(
            model_name='flyerimages',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='create_by_base_user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='flyerimages',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='update_by_base_user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='flyerscheduler',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='created_by_base_user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='flyerscheduler',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='updated_by_base_user', to=settings.AUTH_USER_MODEL),
        ),
    ]
