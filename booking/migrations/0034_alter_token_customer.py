# Generated by Django 4.1.7 on 2024-08-06 07:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0014_alter_customersdocuments_file'),
        ('booking', '0033_alter_booking_token'),
    ]

    operations = [
        migrations.AlterField(
            model_name='token',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='token', to='customer.customers'),
        ),
    ]
