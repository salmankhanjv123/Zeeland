# Generated by Django 4.1.7 on 2024-07-08 14:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0028_rename_amount_banktransaction_deposit_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='banktransaction',
            name='transaction_date',
            field=models.DateField(auto_now_add=True),
        ),
    ]
