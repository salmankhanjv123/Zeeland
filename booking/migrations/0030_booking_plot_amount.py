# Generated by Django 4.1.7 on 2024-07-31 10:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0029_booking_token_token_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='plot_amount',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
    ]