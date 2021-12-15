from datetime import date,datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connections

db = 'presta'
id_shop = 1

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'stock history'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        print (self.help)
        logger.info(self.help)

        today = datetime.today().date() # get a Date object
        logger.info(today)

        self.set_stock_history()

        print('done')
        logger.error("DONE - %s! - %s",self.help,str(today))

    def set_stock_history(self):
        print('set_price_outlet')
        sql="""
SELECT ps.id_shop,ps.id_product,
psa.id_product_attribute, 
COALESCE(
(SELECT IF(REFERENCE='',NULL,REFERENCE) FROM ps17_product_attribute WHERE id_product_attribute=psa.id_product_attribute),
p.reference
) REFERENCE,
COALESCE(
(SELECT IF(ean13='',NULL,ean13) FROM ps17_product_attribute WHERE id_product_attribute=psa.id_product_attribute),
p.ean13
) ean13,
psa.quantity
FROM 
ps17_product_shop ps  
JOIN ps17_product p ON p.id_product=ps.id_product
JOIN ps17_stock_available psa ON p.id_product=psa.id_product AND psa.id_shop=ps.id_shop
WHERE 
ps.id_shop=%s AND ps.active=1
ORDER BY ps.id_product
        """
        result = None
        with connections[db].cursor() as cursor:
            cursor.execute(sql,[id_shop,])
            result = cursor.fetchall()

            n=1
            print (len(result))
            if result and len(result):
                for row in result:
                    print(n,row)
                    cursor.execute(
                        f"""
insert into a_stock_history (date_add,id_shop,id_product,id_product_attribute,reference,ean13,qnt) 
values (date(now()),%s,%s,%s,%s,%s,%s)
on duplicate key update reference=%s,ean13=%s,qnt=%s
                        """
                        ,row+(row[-3],row[-2],row[-1]))
                    n+=1
