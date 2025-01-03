# Generated by Django 4.1.7 on 2023-06-01 08:42

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('customer', '0001_initial'),
        ('projects', '0001_initial'),
        ('plots', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('booking_id', models.CharField(max_length=10)),
                ('reference', models.CharField(max_length=30, null=True)),
                ('reference_contact', models.CharField(max_length=20, null=True)),
                ('booking_date', models.DateField()),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('installment_plan', models.IntegerField()),
                ('due_date', models.DateField()),
                ('installement_date', models.IntegerField()),
                ('installment_per_month', models.FloatField()),
                ('remarks', models.TextField(null=True)),
                ('total_amount', models.FloatField()),
                ('advance', models.FloatField()),
                ('remaining', models.FloatField()),
                ('total_receiving_amount', models.FloatField()),
                ('total_remaining_amount', models.FloatField()),
                ('status', models.CharField(default='active', max_length=10)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='customer.customers')),
                ('plot', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='plots.plots')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='projects.projects')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'booking',
            },
        ),
    ]
