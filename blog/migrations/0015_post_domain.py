# Generated by Django 3.2.15 on 2023-01-20 20:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0014_postlang'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='domain',
            field=models.IntegerField(choices=[(1, 'Co Uk'), (2, 'Eu')], default=1),
        ),
    ]
