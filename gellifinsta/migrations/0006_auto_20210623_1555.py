# Generated by Django 3.2.4 on 2021-06-23 14:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gellifinsta', '0005_rename_remote_fname_gellifinsta_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='gellifinsta',
            name='caption',
            field=models.TextField(blank=True, null=True, verbose_name='Caption'),
        ),
        migrations.AddField(
            model_name='gellifinsta',
            name='tags',
            field=models.TextField(blank=True, null=True, verbose_name='Tags'),
        ),
        migrations.AlterField(
            model_name='gellifinsta',
            name='file_path',
            field=models.CharField(max_length=500, verbose_name='File Path'),
        ),
        migrations.AlterField(
            model_name='gellifinsta',
            name='url',
            field=models.CharField(max_length=500, verbose_name='URL'),
        ),
    ]
