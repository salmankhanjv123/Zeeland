# Generated by Django 4.1.7 on 2024-07-08 11:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0026_bankdeposittransactions_cheque_number_and_more'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='bankdeposit',
            table='bank_deposits',
        ),
    ]