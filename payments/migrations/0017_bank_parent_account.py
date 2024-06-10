# Generated by Django 4.1.7 on 2024-06-10 11:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0016_alter_incomingfund_bank_alter_outgoingfund_bank'),
    ]

    operations = [
        migrations.AddField(
            model_name='bank',
            name='parent_account',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sub_accounts', to='payments.bank'),
        ),
    ]
