# Generated by Django 4.1.7 on 2023-12-11 08:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('plots', '0004_plots_status'),
        ('customer', '0003_customermessages_customermessagesdocuments'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customermessages',
            name='customer',
        ),
        migrations.AddField(
            model_name='customermessages',
            name='plot',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.PROTECT, to='plots.plots'),
            preserve_default=False,
        ),
    ]
