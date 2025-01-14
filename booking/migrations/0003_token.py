# Generated by Django 4.1.7 on 2023-06-08 15:21

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0001_initial'),
        ('customer', '0001_initial'),
        ('plots', '0003_rename_square_feets_plots_square_fts'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('booking', '0002_rename_installement_date_booking_installment_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='Token',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('expire_date', models.DateField()),
                ('amount', models.FloatField()),
                ('remarks', models.TextField(null=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='customer.customers')),
                ('plot', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='plots.plots')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='projects.projects')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
