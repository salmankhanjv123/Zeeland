# Generated by Django 4.1.7 on 2024-07-09 19:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0026_remove_plotresale_customer_amount_paid_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='plotresale',
            name='amount_received',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='plotresale',
            name='remaining',
            field=models.FloatField(default=0),
        ),
    ]