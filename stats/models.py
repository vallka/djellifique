from django.db import models

# Create your models here.
class DailySales(models.Model):
    day = models.CharField(primary_key=True,max_length=20)
    products = models.IntegerField(blank=True,null=True)
    products_discounted = models.IntegerField(blank=True,null=True)
    orders = models.IntegerField(blank=True,null=True)
    GBP_products = models.FloatField(blank=True,null=True)
    GBP_8vat = models.FloatField(blank=True,null=True)
    GBP_products_8vat = models.FloatField(blank=True,null=True)
    gross_margin = models.FloatField(blank=True,null=True)
    gross_margin_percent = models.FloatField(blank=True,null=True)

    @staticmethod
    def SQL(par='d'):
        digits = 4 if par=='y' else 7 if par=='m' else 10

        sql = f"""
SELECT
substr(date_add,1,{digits}) day,
sum((select sum(product_quantity) from ps17_order_detail d where id_order=o.id_order)) products,
sum((select sum(product_quantity) from ps17_order_detail d where id_order=o.id_order and reduction_percent>0)) products_discounted,
count(id_order) orders,
round(sum((total_products_wt-total_discounts_tax_incl)/conversion_rate) ,2) GBP_products,
round(0.08*sum((total_products_wt-total_discounts_tax_incl)/conversion_rate) ,2) GBP_8vat,
round(0.92*sum((total_products_wt-total_discounts_tax_incl)/conversion_rate) ,2) GBP_products_8vat,
round((
0.92*sum((total_products_wt-total_discounts_tax_incl)/conversion_rate)  -
sum((select sum(original_wholesale_price) from ps17_order_detail d where id_order=o.id_order)) 
    ),2) gross_margin
,
round((
(0.92*sum((total_products_wt-total_discounts_tax_incl)/conversion_rate)  -
sum((select sum(original_wholesale_price) from ps17_order_detail d where id_order=o.id_order)) 
) * 100 /
(0.92*sum((total_products_wt-total_discounts_tax_incl)/conversion_rate))
),2) gross_margin_percent

FROM `ps17_orders` o
where current_state in
(2,3,4,5,17,20,21,31,35,39,40)

group by
substr(date_add,1,{digits})
order by 1 
        """

        return sql