# Generated by Django 4.1.7 on 2024-06-12 12:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0022_bankdeposittransactions'),
    ]

    operations = [
        migrations.AddField(
            model_name='bank',
            name='main_type',
            field=models.CharField(default='asset', max_length=100),
            preserve_default=False,
        ),
    ]
