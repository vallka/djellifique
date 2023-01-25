# Generated by Django 3.2.15 on 2023-01-16 21:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0013_post_email_subject'),
    ]

    operations = [
        migrations.CreateModel(
            name='PostLang',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lang_iso_code', models.CharField(max_length=5, verbose_name='Language ISO Code')),
                ('title', models.CharField(default='', max_length=100, verbose_name='Title')),
                ('email_subject', models.CharField(blank=True, default='', max_length=100, verbose_name='Subject')),
                ('text', models.TextField(blank=True, default='', verbose_name='Text')),
                ('description', models.TextField(blank=True, default='', verbose_name='Meta Description')),
                ('keywords', models.TextField(blank=True, default='', verbose_name='Meta Keywords')),
                ('json_ld', models.TextField(blank=True, default='', verbose_name='script ld+json')),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='blog.post')),
            ],
            options={
                'unique_together': {('post', 'lang_iso_code')},
            },
        ),
    ]
