# Generated by Django 4.1.7 on 2023-06-19 09:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0005_alter_booking_plot'),
        ('projects', '0001_initial'),
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentReminder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('remarks', models.TextField(blank=True, null=True)),
                ('reminder_date', models.DateField()),
                ('booking', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='booking.booking')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='projects.projects')),
            ],
        ),
    ]
