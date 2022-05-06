# Generated by Django 3.2.9 on 2022-03-31 13:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0011'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='blog_start_dt',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Published'),
        ),
        migrations.AlterField(
            model_name='post',
            name='email_send_dt',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Sent'),
        ),
    ]