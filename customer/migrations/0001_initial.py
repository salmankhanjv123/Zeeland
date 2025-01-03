# Generated by Django 4.1.7 on 2023-06-01 08:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Customers',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('father_name', models.CharField(max_length=30)),
                ('contact', models.CharField(blank=True, max_length=40, null=True)),
                ('cnic', models.CharField(max_length=16)),
                ('address', models.TextField(blank=True, null=True)),
                ('pic', models.ImageField(blank=True, null=True, upload_to='media/customer')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='projects.projects')),
            ],
            options={
                'db_table': 'customers',
            },
        ),
    ]
