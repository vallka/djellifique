from datetime import date,datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connections
import os

db = 'presta'
id_shop = 1

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'check_customer_certificates'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        print (self.help)
        logger.info(self.help)

        today = datetime.today().date() # get a Date object
        logger.info(today)

        self.check_customer_certificates()

        print('done')
        logger.error("DONE - %s! - %s",self.help,str(today))

    def check_customer_certificates(self):
        print('check_customer_certificates')
        sql="""
SELECT DISTINCT
 c.id_customer,
CONCAT(c.firstname,' ',c.lastname) `name`,
c.email

FROM ps17_customer c
LEFT OUTER JOIN ps17_orders o2 ON c.id_customer=o2.id_customer AND 
o2.current_state IN        (SELECT id_order_state FROM ps17_order_state WHERE paid=1)
WHERE c.id_customer NOT IN 
(SELECT id_customer FROM ps17_customer_group WHERE id_group>=4 
)
AND (o2.date_add>DATE_SUB(NOW(),INTERVAL 1 MONTH)
OR c.date_add>DATE_SUB(NOW(),INTERVAL 1 MONTH)
)

ORDER BY c.id_customer
        """
        result = None
        with connections[db].cursor() as cursor:
            cursor.execute(sql,)
            result = cursor.fetchall()

            n=1
            print (len(result))
            if result and len(result):
                for row in result:
                    email = row[2]
                    # row = (id_shop,id_product,id_product_attribute,reference,ean13,quantity,last_quantity)
                    dirname = os.path.join(settings.MEDIA_ROOT, 'customer-certificates', email)
                    exists_and_not_empty = os.path.isdir(dirname) and bool(os.listdir(dirname))
                    # now you can use `exists_and_not_empty` (True if dir exists and contains at least one entry)
                    print(n,row,dirname,exists_and_not_empty)

                    n+=1
