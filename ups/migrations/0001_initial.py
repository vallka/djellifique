# Generated by Django 3.2.9 on 2022-03-31 13:12

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ShippingNumber',
            fields=[
                ('ReferenceNumber', models.CharField(max_length=200, primary_key=True, serialize=False)),
                ('ShippingNumber', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='UPSParcel',
            fields=[
                ('ReferenceNumber', models.CharField(max_length=200, primary_key=True, serialize=False)),
                ('Description', models.CharField(blank=True, max_length=200, null=True)),
                ('ShipTo_AttentionName', models.CharField(blank=True, max_length=200, null=True)),
                ('ShipTo_Name', models.CharField(blank=True, max_length=200, null=True)),
                ('ShipTo_Address_AddressLine1', models.CharField(blank=True, max_length=200, null=True)),
                ('ShipTo_Address_AddressLine2', models.CharField(blank=True, max_length=200, null=True)),
                ('ShipTo_Address_City', models.CharField(blank=True, max_length=200, null=True)),
                ('ShipTo_Address_CountryCode', models.CharField(blank=True, max_length=200, null=True)),
                ('ShipTo_Address_StateCode', models.CharField(blank=True, max_length=200, null=True)),
                ('ShipTo_Address_PostalCode', models.CharField(blank=True, max_length=200, null=True)),
                ('ShipTo_EMailAddress', models.CharField(blank=True, max_length=200, null=True)),
                ('ShipTo_Phone_Number', models.CharField(blank=True, max_length=200, null=True)),
                ('Package_Weight', models.CharField(blank=True, max_length=200, null=True)),
            ],
        ),
    ]