# Generated by Django 4.1.7 on 2024-06-12 13:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0023_bank_main_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bank',
            name='main_type',
            field=models.CharField(default='asset', max_length=100),
        ),
    ]
