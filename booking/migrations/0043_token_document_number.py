# Generated by Django 4.1.7 on 2024-11-28 00:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0042_rename_new_plot_token_plot'),
    ]

    operations = [
        migrations.AddField(
            model_name='token',
            name='document_number',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
