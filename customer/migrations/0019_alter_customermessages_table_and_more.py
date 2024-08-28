# Generated by Django 4.1.7 on 2024-08-28 11:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0018_department_customers_department'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='customermessages',
            table='customers_messages',
        ),
        migrations.AlterModelTable(
            name='customermessagesdocuments',
            table='customers_messages_documents',
        ),
        migrations.AlterModelTable(
            name='customermessagesreminder',
            table='customer_messages_reminder',
        ),
        migrations.AlterModelTable(
            name='customersdocuments',
            table='customers_documents',
        ),
        migrations.AlterModelTable(
            name='dealers',
            table='dealers',
        ),
        migrations.AlterModelTable(
            name='dealersdocuments',
            table='dealers_documents',
        ),
        migrations.AlterModelTable(
            name='department',
            table='departments',
        ),
    ]
