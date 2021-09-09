from django.db import models

# Create your models here.
class UPSParcel(models.Model):
    ReferenceNumber = models.CharField(max_length=200,primary_key=True)
    Description = models.CharField(max_length=200,blank=True,null=True)
    ShipTo_AttentionName = models.CharField(max_length=200,blank=True,null=True)
    ShipTo_Name = models.CharField(max_length=200,blank=True,null=True)
    ShipTo_Address_AddressLine1 = models.CharField(max_length=200,blank=True,null=True)
    ShipTo_Address_AddressLine2 = models.CharField(max_length=200,blank=True,null=True)
    ShipTo_Address_City = models.CharField(max_length=200,blank=True,null=True)
    ShipTo_Address_CountryCode = models.CharField(max_length=200,blank=True,null=True)
    ShipTo_Address_StateCode = models.CharField(max_length=200,blank=True,null=True)
    ShipTo_Address_PostalCode = models.CharField(max_length=200,blank=True,null=True)
    ShipTo_EMailAddress = models.CharField(max_length=200,blank=True,null=True)
    ShipTo_Phone_Number = models.CharField(max_length=200,blank=True,null=True)
    Package_Weight = models.CharField(max_length=200,blank=True,null=True)
    #declared_value_currency = models.CharField(max_length=200,blank=True,null=True)
    #declared_value = models.CharField(max_length=200,blank=True,null=True)

    @staticmethod
    def UPS_sql(ids):
        sql = f"""
            SELECT
                o.reference ReferenceNumber,
                concat(a.firstname,' ',a.lastname) Description,
                concat(a.firstname,' ',a.lastname) ShipTo_AttentionName,
                if (a.company!='',a.company,concat(a.firstname,' ',a.lastname,' ','Nails')) ShipTo_Name,
                COALESCE(a.address1,'') ShipTo_Address_AddressLine1,
                COALESCE(a.address2,'') ShipTo_Address_AddressLine2,
                COALESCE(a.city,'') ShipTo_Address_City,
                COALESCE(if (a.id_country!=17,(select iso_code from ps17_state where id_state=a.id_state),''),'') ShipTo_Address_StateCode,
                (select iso_code from ps17_country where id_country=a.id_country) ShipTo_Address_CountryCode,
                COALESCE(a.postcode,'') ShipTo_Address_PostalCode,
                c.email ShipTo_EMailAddress,
                COALESCE(IF(a.phone='',NULL,a.phone),a.phone_mobile) ShipTo_Phone_Number,
                (select sum(product_weight*product_quantity) from ps17_order_detail d where d.id_order=o.id_order) Package_Weight
            FROM ps17_orders o
                join ps17_address a on a.id_address=o.id_address_delivery
                join ps17_customer c on o.id_customer=c.id_customer			
            WHERE 
        """
        
        if ids=='' or ids=='*' or ids==' ':
            sql +="""
                    id_carrier in (270,273)
                    and 
                    current_state=31
            """
        else:
            ida = ids.split(',')
            map(lambda x:f"'{x}'" ,ida)
            ids = ','.join(ida)

            sql += f"o.id_order in ({ids})"

        sql += " ORDER BY o.id_order"

        return sql

class ShippingNumber(models.Model):
    ReferenceNumber = models.CharField(max_length=200,primary_key=True)
    ShippingNumber = models.CharField(max_length=200)

    @staticmethod
    def ShippingNumber_sql(ids):
        sql = f"""
            SELECT
                o.reference ReferenceNumber,
                o.shipping_number ShippingNumber
            FROM ps17_orders o
            WHERE 
        """
        
        if ids=='':
            sql +="""
                    id_carrier in (270,273)
                    and 
                    current_state=31
            """
        else:
            ida = ids.split(',')
            map(lambda x:f"'{x}'" ,ida)
            ids = ','.join(ida)

            sql += f"o.id_order in ({ids})"

        sql += " ORDER BY o.id_order"

        return sql
