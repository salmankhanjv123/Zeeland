# Generated by Django 4.1.7 on 2024-08-26 16:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0045_chequeclearance_chequeclearancedetail'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChequeClearanceDocuments',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='media/cheque_clearance_files')),
                ('description', models.TextField()),
                ('type', models.CharField(max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cheque_clearance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='files', to='payments.chequeclearance')),
            ],
        ),
    ]
