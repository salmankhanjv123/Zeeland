# Generated by Django 4.1.7 on 2024-10-10 03:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0005_rename_details_balancesheetamountdetails_detail'),
    ]

    operations = [
        migrations.AddField(
            model_name='projects',
            name='cost_per_marla',
            field=models.FloatField(default=0),
        ),
    ]
