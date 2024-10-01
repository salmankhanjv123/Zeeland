# Generated by Django 4.1.7 on 2024-10-01 08:55

from django.db import migrations, models

def transfer_plot_to_plots(apps, schema_editor):
    Booking = apps.get_model('booking', 'Booking')
    for booking in Booking.objects.all():
        if booking.plot:
            booking.new_plots.add(booking.plot)
class Migration(migrations.Migration):

    dependencies = [
        ('plots', '0009_alter_plotsdocuments_table'),
        ('booking', '0036_alter_bookingdocuments_table_alter_plotresale_table_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='new_plots',
            field=models.ManyToManyField(to='plots.plots'),
        ),
        migrations.RunPython(transfer_plot_to_plots),
    ]
