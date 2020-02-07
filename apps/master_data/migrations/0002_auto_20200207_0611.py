# Generated by Django 3.0.3 on 2020-02-07 06:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('master_data', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='billinggroup',
            old_name='slug',
            new_name='code',
        ),
        migrations.RenameField(
            model_name='billingsubgroup',
            old_name='slug',
            new_name='code',
        ),
        migrations.RemoveField(
            model_name='billinggroup',
            name='name',
        ),
        migrations.RemoveField(
            model_name='billingsubgroup',
            name='name',
        ),
        migrations.RemoveField(
            model_name='hospital',
            name='distance',
        ),
        migrations.RemoveField(
            model_name='hospital',
            name='latitude',
        ),
        migrations.RemoveField(
            model_name='hospital',
            name='longitude',
        ),
        migrations.RemoveField(
            model_name='hospital',
            name='profit_center',
        ),
        migrations.AddField(
            model_name='billinggroup',
            name='code_abbreviation',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='billinggroup',
            name='description',
            field=models.TextField(default='Billing Group Description', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='billingsubgroup',
            name='billing_group',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.PROTECT, to='master_data.BillingGroup'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='billingsubgroup',
            name='code_abbreviation',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='billingsubgroup',
            name='code_translation',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='billingsubgroup',
            name='description',
            field=models.TextField(default='Billing Sub Group Description', max_length=100),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='hospital',
            name='address',
            field=models.TextField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='hospital',
            name='code',
            field=models.SlugField(unique=True),
        ),
        migrations.AlterField(
            model_name='hospital',
            name='description',
            field=models.TextField(max_length=100),
        ),
    ]
