# Generated by Django 4.1.7 on 2024-08-28 12:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0049_alter_bankdepositdetail_table_and_more'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='bankdepositdetail',
            table='bank_deposits_details',
        ),
    ]
