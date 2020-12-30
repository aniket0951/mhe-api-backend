# Generated by Django 3.0.3 on 2020-12-22 11:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0027_auto_20201218_1743'),
    ]

    operations = [
        migrations.RenameField(
            model_name='payment',
            old_name='invoice_id',
            new_name='razor_order_id',
        ),
        migrations.RenameField(
            model_name='payment',
            old_name='payment_id',
            new_name='razor_payment_id',
        ),
        migrations.RenameField(
            model_name='paymentrefund',
            old_name='int_payment_id',
            new_name='razor_payment_id',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='order_id',
        ),
        migrations.AddField(
            model_name='payment',
            name='razor_invoice_id',
            field=models.CharField(blank=True, default='0', max_length=50, null=True),
        ),
    ]