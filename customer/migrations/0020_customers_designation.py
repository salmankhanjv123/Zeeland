# Generated by Django 4.1.7 on 2024-10-16 06:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0019_alter_customermessages_table_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customers',
            name='designation',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
