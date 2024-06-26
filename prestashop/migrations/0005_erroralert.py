# Generated by Django 4.1.7 on 2024-05-03 11:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prestashop', '0004_productnote_domain'),
    ]

    operations = [
        migrations.CreateModel(
            name='ErrorAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('domain', models.CharField(max_length=100)),
                ('error_type', models.CharField(max_length=100)),
                ('text', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
