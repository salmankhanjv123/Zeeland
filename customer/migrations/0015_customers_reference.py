# Generated by Django 4.1.7 on 2024-08-15 11:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0014_alter_customersdocuments_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='customers',
            name='reference',
            field=models.CharField(default='customer', max_length=15),
        ),
    ]
