# Generated by Django 4.1.7 on 2024-05-31 11:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0015_bank_account_type_bank_balance_bank_description_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='incomingfund',
            name='bank',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='payments', to='payments.bank'),
        ),
        migrations.AlterField(
            model_name='outgoingfund',
            name='bank',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='expenses', to='payments.bank'),
        ),
    ]