# Generated by Django 4.1.7 on 2023-08-30 12:22

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("booking", "0005_alter_booking_plot"),
    ]

    operations = [
        migrations.AlterField(
            model_name="booking",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="booking",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name="token",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="token",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
