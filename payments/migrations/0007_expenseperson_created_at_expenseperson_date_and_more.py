# Generated by Django 4.1.7 on 2024-03-01 17:25

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0006_rename_advnace_payment_incomingfund_advance_payment'),
    ]

    operations = [
        migrations.AddField(
            model_name='expenseperson',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='expenseperson',
            name='date',
            field=models.DateField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='expenseperson',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
