# Generated by Django 4.1.7 on 2024-05-22 08:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0007_expenseperson_created_at_expenseperson_date_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bank',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
            ],
        ),
        migrations.AddField(
            model_name='incomingfund',
            name='payment_type',
            field=models.CharField(default='cash', max_length=20),
            preserve_default=False,
        ),
    ]