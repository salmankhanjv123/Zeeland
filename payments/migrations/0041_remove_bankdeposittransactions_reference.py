# Generated by Django 4.1.7 on 2024-08-24 00:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0040_alter_journalentryline_person'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bankdeposittransactions',
            name='reference',
        ),
    ]
