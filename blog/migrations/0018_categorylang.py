# Generated by Django 3.2.20 on 2023-08-21 22:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0017_post_email_subsubject'),
    ]

    operations = [
        migrations.CreateModel(
            name='CategoryLang',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lang_iso_code', models.CharField(max_length=5, verbose_name='Language ISO Code')),
                ('category_text', models.CharField(default='', max_length=100, verbose_name='Category')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='blog.category')),
            ],
        ),
    ]
