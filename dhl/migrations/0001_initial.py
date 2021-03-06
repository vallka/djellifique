# Generated by Django 3.2.12 on 2022-05-13 15:14

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DHLParcel',
            fields=[
                ('name_ship_from', models.CharField(blank=True, max_length=200, null=True)),
                ('company_ship_from', models.CharField(blank=True, max_length=200, null=True)),
                ('address_1_ship_from', models.CharField(blank=True, max_length=200, null=True)),
                ('address_2_ship_from', models.CharField(blank=True, max_length=200, null=True)),
                ('address_3_ship_from', models.CharField(blank=True, max_length=200, null=True)),
                ('house_number_ship_from', models.CharField(blank=True, max_length=200, null=True)),
                ('postal_code_ship_from', models.CharField(blank=True, max_length=200, null=True)),
                ('city_ship_from', models.CharField(blank=True, max_length=200, null=True)),
                ('country_code_ship_from', models.CharField(blank=True, max_length=200, null=True)),
                ('email_address_ship_from', models.CharField(blank=True, max_length=200, null=True)),
                ('phone_country_code_ship_from', models.CharField(blank=True, max_length=200, null=True)),
                ('phone_number_ship_from', models.CharField(blank=True, max_length=200, null=True)),
                ('name_ship_to', models.CharField(blank=True, max_length=200, null=True)),
                ('company_ship_to', models.CharField(blank=True, max_length=200, null=True)),
                ('address_1_ship_to', models.CharField(blank=True, max_length=200, null=True)),
                ('address_2_ship_to', models.CharField(blank=True, max_length=200, null=True)),
                ('address_3_ship_to', models.CharField(blank=True, max_length=200, null=True)),
                ('house_number_ship_to', models.CharField(blank=True, max_length=200, null=True)),
                ('postal_code_ship_to', models.CharField(blank=True, max_length=200, null=True)),
                ('city_ship_to', models.CharField(blank=True, max_length=200, null=True)),
                ('state_code_ship_to', models.CharField(blank=True, max_length=200, null=True)),
                ('country_code_ship_to', models.CharField(blank=True, max_length=200, null=True)),
                ('email_address_ship_to', models.CharField(blank=True, max_length=200, null=True)),
                ('phone_country_code_ship_to', models.CharField(blank=True, max_length=200, null=True)),
                ('phone_number_ship_to', models.CharField(blank=True, max_length=200, null=True)),
                ('account_number_shipper', models.CharField(blank=True, max_length=200, null=True)),
                ('total_weight', models.CharField(blank=True, max_length=200, null=True)),
                ('declared_value_currency', models.CharField(blank=True, max_length=200, null=True)),
                ('declared_value', models.CharField(blank=True, max_length=200, null=True)),
                ('product_code_3_letter', models.CharField(blank=True, max_length=200, null=True)),
                ('summary_of_contents', models.CharField(blank=True, max_length=200, null=True)),
                ('shipment_type', models.CharField(blank=True, max_length=200, null=True)),
                ('shipment_reference', models.CharField(max_length=200, primary_key=True, serialize=False)),
                ('total_shipment_pieces', models.CharField(blank=True, max_length=200, null=True)),
                ('invoice_type', models.CharField(blank=True, max_length=200, null=True)),
                ('length', models.CharField(blank=True, max_length=200, null=True)),
                ('width', models.CharField(blank=True, max_length=200, null=True)),
                ('depth', models.CharField(blank=True, max_length=200, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ShippingNumber',
            fields=[
                ('ReferenceNumber', models.CharField(max_length=200, primary_key=True, serialize=False)),
                ('ShippingNumber', models.CharField(max_length=200)),
            ],
        ),
    ]
