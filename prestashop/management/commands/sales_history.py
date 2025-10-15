from datetime import date,datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connections
from icecream import ic

db = 'presta'
id_shop = 1

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'sales history'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        print (self.help)
        #logger.info(self.help)

        today = datetime.today().date() # get a Date object
        #logger.info(today)

        #date1 = date(2025, 9, 1)
        #date2 = date(2025, 9, 5)
        date1 = today - timedelta(days=3)
        date2 = today
        current_date = date1
        while current_date < date2:
            ic(current_date)
            self.set_sales_history(current_date)
            current_date += timedelta(days=1)
        


        print('done')
        #logger.error("DONE - %s! - %s",self.help,str(today))

    def set_sales_history(self,the_date):
        print('set_sales_history')
        sql="""
SELECT id_shop,id_product,id_product_attribute,SUM(product_quantity) sold,SUM(packed_quantity) sold_in_pack,DATE(MIN(DATE_ADD) ) date_add
FROM
(
SELECT 
od.product_id AS id_product,
product_attribute_id AS id_product_attribute,
o.id_order,od.product_quantity,p.product_type,o.current_state,NULL AS id_pack,o.id_shop,0 AS packed_quantity,o.date_add
FROM ps17_orders o
JOIN ps17_order_detail od ON o.id_order=od.id_order
LEFT JOIN ps17_product p ON od.product_id=p.id_product

UNION ALL

SELECT 
pp.id_product,
pa.id_product_attribute_item AS id_product_attribute,
o.id_order,od.product_quantity*pa.quantity AS product_quantity,pp.product_type,o.current_state,p.id_product AS id_pack,o.id_shop,od.product_quantity*pa.quantity AS packed_quantity,o.date_add

FROM ps17_orders o
JOIN ps17_order_detail od ON o.id_order=od.id_order
JOIN ps17_product p ON od.product_id=p.id_product
LEFT OUTER JOIN ps17_pack pa ON p.id_product=pa.id_product_pack AND p.product_type='pack'
LEFT OUTER JOIN ps17_product pp  ON pp.id_product=pa.id_product_item
WHERE 
p.product_type='pack'
) qq

WHERE current_state IN (SELECT id_order_state FROM ps17_order_state WHERE paid=1)
AND NOT EXISTS (SELECT id_order_history FROM ps17_order_history WHERE id_order=qq.id_order AND id_order_state IN (29,30))
AND DATE(DATE_ADD)=%s
GROUP BY id_product,id_product_attribute        
"""
        result = None
        with connections[db].cursor() as cursor:
            cursor.execute(sql,[the_date,])
            result = cursor.fetchall()

            n=1
            print (len(result))
            if result and len(result):
                for row in result:
                    print(n,row)
                    cursor.execute(
                        """
insert into a_product_sales (id_shop,id_product,id_product_attribute,sold,sold_in_pack,date_add)
values (%s,%s,%s,%s,%s,%s)
on duplicate key update
sold=values(sold),
sold_in_pack=values(sold_in_pack),
date_add=values(date_add)
                        """,
                        row
                    )
                    n+=1
