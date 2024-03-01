# Generated by Django 4.1.7 on 2024-03-01 18:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0007_customermessages_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomerMessagesReminder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('follow_up_message', models.TextField(blank=True, null=True)),
                ('status', models.CharField(default='pending', max_length=20)),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reminders', to='customer.customermessages')),
            ],
        ),
    ]
