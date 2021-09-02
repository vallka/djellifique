# Generated by Django 3.1 on 2020-08-28 13:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(blank=True, max_length=100, unique=True, verbose_name='Category')),
                ('slug', models.SlugField(blank=True, max_length=100, unique=True, verbose_name='Slug')),
            ],
            options={
                'ordering': ['slug'],
            },
        ),
    ]
