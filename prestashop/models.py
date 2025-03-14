import requests
import json
from django.db import models

# Create your models here.
class Ps17Product(models.Model):
    id_product = models.AutoField(primary_key=True)
    id_supplier = models.PositiveIntegerField(blank=True, null=True)
    id_manufacturer = models.PositiveIntegerField(blank=True, null=True)
    id_category_default = models.PositiveIntegerField(blank=True, null=True)
    id_shop_default = models.PositiveIntegerField()
    id_tax_rules_group = models.PositiveIntegerField()
    on_sale = models.PositiveIntegerField()
    online_only = models.PositiveIntegerField()
    ean13 = models.CharField(max_length=13, blank=True, null=True)
    isbn = models.CharField(max_length=32, blank=True, null=True)
    upc = models.CharField(max_length=12, blank=True, null=True)
    ecotax = models.DecimalField(max_digits=17, decimal_places=6)
    quantity = models.IntegerField()
    minimal_quantity = models.PositiveIntegerField()
    low_stock_threshold = models.IntegerField(blank=True, null=True)
    low_stock_alert = models.IntegerField()
    price = models.DecimalField(max_digits=20, decimal_places=6)
    wholesale_price = models.DecimalField(max_digits=20, decimal_places=6)
    unity = models.CharField(max_length=255, blank=True, null=True)
    unit_price_ratio = models.DecimalField(max_digits=20, decimal_places=6)
    additional_shipping_cost = models.DecimalField(max_digits=20, decimal_places=2)
    reference = models.CharField(max_length=64, blank=True, null=True)
    supplier_reference = models.CharField(max_length=32, blank=True, null=True)
    location = models.CharField(max_length=64, blank=True, null=True)
    width = models.DecimalField(max_digits=20, decimal_places=6)
    height = models.DecimalField(max_digits=20, decimal_places=6)
    depth = models.DecimalField(max_digits=20, decimal_places=6)
    weight = models.DecimalField(max_digits=20, decimal_places=6)
    out_of_stock = models.PositiveIntegerField()
    additional_delivery_times = models.PositiveIntegerField()
    quantity_discount = models.IntegerField(blank=True, null=True)
    customizable = models.IntegerField()
    uploadable_files = models.IntegerField()
    text_fields = models.IntegerField()
    active = models.PositiveIntegerField()
    redirect_type = models.CharField(max_length=12)
    id_type_redirected = models.PositiveIntegerField()
    available_for_order = models.IntegerField()
    available_date = models.DateField(blank=True, null=True)
    show_condition = models.IntegerField()
    condition = models.CharField(max_length=11)
    show_price = models.IntegerField()
    indexed = models.IntegerField()
    visibility = models.CharField(max_length=7)
    cache_is_pack = models.IntegerField()
    cache_has_attachments = models.IntegerField()
    is_virtual = models.IntegerField()
    cache_default_attribute = models.PositiveIntegerField(blank=True, null=True)
    date_add = models.DateTimeField()
    date_upd = models.DateTimeField()
    advanced_stock_management = models.IntegerField()
    pack_stock_type = models.PositiveIntegerField()
    state = models.PositiveIntegerField()

    class Meta:
        managed = False
        db_table = 'ps17_product'




class Ps17ProductLang(models.Model):
    id_product = models.PositiveIntegerField(primary_key=True)
    id_shop = models.PositiveIntegerField()
    id_lang = models.PositiveIntegerField()
    description = models.TextField(blank=True, null=True)
    description_short = models.TextField(blank=True, null=True)
    link_rewrite = models.CharField(max_length=128)
    meta_description = models.CharField(max_length=512, blank=True, null=True)
    meta_keywords = models.CharField(max_length=255, blank=True, null=True)
    meta_title = models.CharField(max_length=128, blank=True, null=True)
    name = models.CharField(max_length=128)
    available_now = models.CharField(max_length=255, blank=True, null=True)
    available_later = models.CharField(max_length=255, blank=True, null=True)
    delivery_in_stock = models.CharField(max_length=255, blank=True, null=True)
    delivery_out_stock = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ps17_product_lang'
        unique_together = (('id_product', 'id_shop', 'id_lang'),)


class Order(models.Model):
    class Meta:
        managed = False
        db_table = 'ps17_orders'

    id_order = models.PositiveIntegerField(primary_key=True,editable=False,db_column=None)
    reference = models.CharField(max_length=255, blank=True, null=True,editable=False,)
    id_order_state = models.PositiveIntegerField(blank=True, null=True,editable=False,)
    order_state = models.CharField(max_length=255, blank=True, null=True,editable=False,)
    shipping_number = models.CharField(max_length=255, blank=True, null=True,editable=False,)
    firstname_customer = models.CharField(max_length=255, blank=True, null=True,editable=False,)
    lastname_customer = models.CharField(max_length=255, blank=True, null=True,editable=False,)
    note = models.TextField(blank=True, null=True,editable=False,)
    firstname = models.CharField(max_length=255, blank=True, null=True,editable=False,)
    lastname = models.CharField(max_length=255, blank=True, editable=False,)
    email = models.CharField(max_length=255, blank=True, editable=False,)
    postcode = models.CharField(max_length=255, blank=True, editable=False,)
    address1 = models.CharField(max_length=255, blank=True, editable=False,)
    address2 = models.CharField(max_length=255, blank=True, editable=False,)
    city = models.CharField(max_length=255, blank=True, editable=False,)
    phone = models.CharField(max_length=255, blank=True, editable=False,)
    country = models.CharField(max_length=255, blank=True, editable=False,)
    currency_code = models.CharField(max_length=3, blank=True, editable=False,)
    total_paid  = models.DecimalField(blank=True, editable=False,max_digits=6, decimal_places=2)
    total_products_wt   = models.FloatField(blank=True, editable=False,)
    total_shipping_tax_incl  = models.FloatField(blank=True, editable=False,)
    date_add  = models.DateTimeField(blank=True, editable=False,)
    date_upd  = models.DateTimeField(blank=True, editable=False,)
    id_country = models.PositiveIntegerField(blank=True, editable=False,)
    carrier = models.CharField(max_length=255, blank=True, editable=False,)
    is_new = models.PositiveIntegerField(blank=True, editable=False,)

    @staticmethod
    def SQL(one=False):
        sql = """
    SELECT 
        id_order,
        reference,
        o.current_state as id_order_state
        ,(select name from ps17_order_state_lang where id_lang=1 and id_order_state=o.current_state) order_state
        ,o.shipping_number
        ,c.firstname as firstname_customer,
        c.lastname as lastname_customer,
        c.note
        ,a.firstname,
        a.lastname
        ,c.email,
        a.postcode,
        a.address1,
        a.address2,
        a.city,
        a.phone
        ,(select name from ps17_country_lang where id_lang=1 and id_country=a.id_country) country
        ,iso_code as currency_code
        ,total_paid ,total_products_wt ,total_shipping_tax_incl,o.date_add,o.date_upd
        ,o.id_customer,o.id_address_delivery,a.id_country
        ,ca.name as carrier
        ,IF((SELECT so.id_order FROM `ps17_orders` so WHERE so.id_customer = o.id_customer AND so.id_order < o.id_order LIMIT 1) > 0, 0, 1) as is_new,
        (SELECT id_order FROM ps17_orders o_prev WHERE o_prev.id_order<o.id_order ORDER BY id_order DESC LIMIT 1) AS id_order_prev,
        (SELECT id_order FROM ps17_orders o_prev WHERE o_prev.id_order>o.id_order ORDER BY id_order ASC LIMIT 1) AS id_order_next
        FROM `ps17_orders` o
        JOIN ps17_customer c on o.id_customer=c.id_customer
        JOIN ps17_address a on id_address_delivery=a.id_address
        join ps17_carrier ca on ca.id_carrier=o.id_carrier
        join ps17_currency cu on cu.id_currency=o.id_currency
        WHERE o.date_add>=DATE_SUB(NOW(),INTERVAL 1 MONTH)
"""
        #WHERE o.current_state in (2,3,17,20,21,31,39,40)
        if one:
            sql += " AND o.id_order=%s " 
        else:
            sql += " ORDER BY id_order DESC "

        return sql        

class OrderDetail(models.Model):
    class Meta:
        managed = False
        db_table = 'ps17_order_detail'

    id_order_detail = models.PositiveIntegerField(primary_key=True,editable=False,db_column=None)
    product_id = models.PositiveIntegerField(editable=False,db_column=None)
    product_reference = models.CharField(max_length=255, blank=True, null=True,editable=False,)
    product_name = models.CharField(max_length=255, blank=True, null=True,editable=False,)
    product_ean13 = models.CharField(max_length=255, blank=True, null=True,editable=False,)
    product_type = models.CharField(max_length=255, blank=True, null=True,editable=False,)
    product_quantity = models.PositiveIntegerField(editable=False,db_column=None)
    att_name = models.CharField(max_length=255, blank=True, null=True,editable=False,)
    id_image = models.PositiveIntegerField(editable=False,db_column=None)
    quantity = models.IntegerField(editable=False,db_column=None)
    proc_quantity = models.IntegerField(editable=False,db_column=None)
    proc_quantity_set = models.IntegerField(editable=False,db_column=None)

    @staticmethod
    def SQL():
        return """
SELECT odd.id_order_detail,odd.product_id,odd.product_reference,odd.product_name,
COALESCE((SELECT ean13 FROM ps17_product_attribute att WHERE att.id_product_attribute=odd.product_attribute_id),odd.product_ean13) product_ean13
,odd.product_type,odd.product_quantity,
IF(product_attribute_id=0,'',
(SELECT NAME FROM ps17_product_attribute_combination pac 
JOIN ps17_attribute_lang atl ON atl.id_attribute=pac.id_attribute AND atl.id_lang=1
WHERE pac.id_product_attribute=odd.product_attribute_id 
)
) AS att_name,
COALESCE(
(SELECT ai.id_image FROM ps17_product_attribute_image ai,ps17_image ai2 WHERE odd.product_attribute_id=ai.id_product_attribute AND ai.id_image=ai2.id_image ORDER BY POSITION LIMIT 1),
i.id_image) AS id_image,
a.quantity ,proc_quantity,proc_quantity_set,id_pack

FROM (

SELECT 
od.id_order_detail,
od.product_id AS product_id,od.product_reference AS product_reference,od.product_name,p.ean13 AS product_ean13,od.product_quantity,p.product_type,NULL AS id_pack
,o.id_order,o.id_shop
,od.product_attribute_id
FROM ps17_orders o
JOIN ps17_order_detail od ON o.id_order=od.id_order
JOIN ps17_product p ON od.product_id=p.id_product

UNION ALL

SELECT 
od.id_order_detail,
pp.id_product AS product_id,pp.reference AS product_reference,
CONCAT(od.product_name,'// ',pl.name) AS product_name,pp.ean13 AS product_ean13,
od.product_quantity*pa.quantity AS product_quantity,pp.product_type,p.id_product AS id_pack
,o.id_order,o.id_shop
,pa.id_product_attribute_item AS product_attribute_id
FROM ps17_orders o
JOIN ps17_order_detail od ON o.id_order=od.id_order
JOIN ps17_product p ON od.product_id=p.id_product
LEFT OUTER JOIN ps17_pack pa ON p.id_product=pa.id_product_pack AND p.product_type='pack'
LEFT OUTER JOIN ps17_product pp  ON pp.id_product=pa.id_product_item
LEFT OUTER JOIN ps17_product_lang pl  ON pl.id_product=pa.id_product_item AND pl.id_lang=1 AND pl.id_shop=o.id_shop

WHERE 
p.product_type='pack'

) odd
LEFT OUTER JOIN ps17_image i ON odd.product_id=i.id_product AND i.cover=1 
LEFT OUTER JOIN ps17_stock_available a ON a.id_product=odd.product_id AND a.id_product_attribute=odd.product_attribute_id AND a.id_shop=odd.id_shop


LEFT OUTER JOIN (
SELECT id_product,SUM(product_quantity) proc_quantity,SUM(packed_quantity) proc_quantity_set
FROM 
(


SELECT oo.id_product,oo.id_order,oo.product_quantity,oo.packed_quantity  FROM
(
SELECT 
od.product_id AS id_product,o.id_order,od.product_quantity,p.product_type,o.current_state,o.date_upd,NULL AS id_pack,o.id_shop,0 AS packed_quantity
FROM ps17_orders o
JOIN ps17_order_detail od ON o.id_order=od.id_order
JOIN ps17_product p ON od.product_id=p.id_product

UNION ALL

SELECT 
pp.id_product,o.id_order,od.product_quantity*pa.quantity AS product_quantity,pp.product_type,o.current_state,o.date_upd,p.id_product AS id_pack,o.id_shop,od.product_quantity*pa.quantity AS packed_quantity
FROM ps17_orders o
JOIN ps17_order_detail od ON o.id_order=od.id_order
JOIN ps17_product p ON od.product_id=p.id_product
LEFT OUTER JOIN ps17_pack pa ON p.id_product=pa.id_product_pack AND p.product_type='pack'
LEFT OUTER JOIN ps17_product pp  ON pp.id_product=pa.id_product_item
WHERE 
p.product_type='pack'

) oo
WHERE
current_state IN (2,3,9,11,12,17,20,21,22,23,24,25,26,27,31,39,40)
AND oo.date_upd>DATE_SUB(NOW(),INTERVAL 1 MONTH)
AND oo.id_shop=1


) agg
GROUP BY agg.id_product
) aggg ON aggg.id_product=odd.product_id


WHERE id_order=%s
ORDER BY product_name

"""

#        return """
#SELECT 
#p.id_order_detail,
#p.product_id as id_product,
#pr.reference as product_reference,
#p.product_name,
#pr.ean13 as product_ean13,
#p.product_quantity,
#IF(pr.product_type='pack',(SELECT COUNT(*) FROM ps17_pack WHERE id_product_pack=p.product_id),1) AS unity,
#a.quantity,
#i.id_image
#	FROM ps17_order_detail p 
#	left outer join ps17_image i on p.product_id=i.id_product and i.cover=1 
#	left outer join ps17_stock_available a on a.id_product=p.product_id and 	
#	a.id_product_attribute=p.product_attribute_id and a.id_shop=(select id_shop from ps17_orders where id_order=p.id_order)
#    left outer join ps17_product pr on pr.id_product=p.product_id	
#	WHERE id_order=%s order by product_name
#"""





class ProductNote(models.Model):
    id_product = models.PositiveIntegerField()
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,)
    created_by = models.PositiveIntegerField()
    
    class Domains(models.IntegerChoices):
        CO_UK = 1
        EU = 2

    domain = models.IntegerField(default=Domains.CO_UK,choices=Domains.choices)

class PrintCategory:
    
    def __init__(self,id_category,host) -> None:
        self.host = host

        if '127.0.0.1' in host or 'gellifique.eu' in host:
            server = 'www.gellifique.eu'
        else:
            server = 'www.gellifique.co.uk'

        self.id = id_category

        h={'Accept':'application/json, text/javascript, */*; q=0.01'}
        r=requests.get(f'https://{server}/category({id_category})?order=product.position.asc',headers=h)

        print(r)

        self.response = json.loads(r.text)

        #print(self.response.keys())

        #print(self.response['products'][0]["id_product"])
        #print(self.response['products'][0]["price"])
        #print(self.response['products'][0]["name"])
        #print(self.response['products'][0]["reference"])
        #print(self.response['products'][0]["description_short"])
        #print(self.response['products'][0]["cover"]["bySize"]["large_default"]["url"])

        self.products = self.response['products']

        print(len(self.products))

        self.rendered_products_header = self.response['rendered_products_header']
        self.rendered_products = self.response['rendered_products'].replace(' (HEMA FREE)','')

class ErrorAlert(models.Model):
    domain = models.CharField(max_length=100)
    error_type = models.CharField(max_length=100)
    text = models.TextField(blank=True, null=True)
    error_dt = models.DateTimeField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True,)

class ProductInventory(models.Model):
    id_product = models.PositiveIntegerField()
    inventory_type = models.CharField(max_length=100)
    value = models.CharField(max_length=255)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    
    class Domains(models.IntegerChoices):
        CO_UK = 1
        EU = 2

    domain = models.IntegerField(default=Domains.CO_UK,choices=Domains.choices)
