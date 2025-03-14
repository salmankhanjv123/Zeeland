# Generated by Django 4.1.7 on 2024-02-22 12:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0011_alter_plotresale_company_amount_paid_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='booking_type',
            field=models.CharField(default='installement payment', max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='booking',
            name='follow_up_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='booking',
            name='due_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
