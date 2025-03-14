# Generated by Django 4.1.7 on 2024-07-24 13:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0028_plotresale_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='token',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='booking.token'),
        ),
        migrations.AddField(
            model_name='token',
            name='status',
            field=models.CharField(default='pending', max_length=10),
        ),
    ]
