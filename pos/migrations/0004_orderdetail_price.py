# Generated by Django 3.2.12 on 2022-06-11 19:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0003_alter_product_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderdetail',
            name='price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=8, verbose_name='price'),
            preserve_default=False,
        ),
    ]
