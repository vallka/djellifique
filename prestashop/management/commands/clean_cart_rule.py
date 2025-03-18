from datetime import date,datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connections

db = 'presta'
id_shop = 1

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'clean_cart_rule'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        global db,id_shop
        print (self.help)
        logger.info(self.help)

        today = datetime.today().date() # get a Date object
        logger.info(today)

        db = 'presta_eu'
        self.clean_cart_rule()
        db = 'presta'
        self.clean_cart_rule()

        print('done')
        logger.error("DONE - %s! - %s",self.help,str(today))

    def clean_cart_rule(self):
        print('clean_cart_rule-',db)
        sql="""
SELECT cr.id_cart_rule,cr.id_customer,ccr.id_cart_rule,crl.name,cr.code,o.id_order,o.id_cart,
DATE_FORMAT(o.date_add,'%Y-%m-%d %H:%i') as date_add,
DATE_FORMAT(cr.date_from,'%Y-%m-%d %H:%i') as date_from,
DATE_FORMAT(cr.date_to,'%Y-%m-%d %H:%i') as date_to,quantity
FROM ps17_cart_rule cr 
LEFT OUTER JOIN ps17_cart_rule_lang crl ON cr.id_cart_rule=crl.id_cart_rule AND id_lang=1
LEFT OUTER JOIN ps17_cart_cart_rule ccr ON cr.id_cart_rule=ccr.id_cart_rule
LEFT OUTER JOIN ps17_orders o ON o.id_cart=ccr.id_cart
WHERE (cr.quantity<1 OR date_to<DATE_SUB(NOW(),INTERVAL 1 MONTH))
ORDER BY 1
LIMIT 100
        """
        result = None
        with connections[db].cursor() as cursor:
            cursor.execute(sql)
            result = cursor.fetchall()

            n=1
            print (len(result))
            if result and len(result):
                print('id_cart_rule,id_customer,id_cart_rule,name,code,id_order,id_cart,date_add,date_from,date_to,quantity')
                for row in result:
                    print(row)
                    cursor.execute(f"DELETE FROM ps17_cart_rule_combination  WHERE id_cart_rule_1=%s OR id_cart_rule_2=%s",[row[0],row[0]])
                    cursor.execute(f"DELETE FROM ps17_cart_rule_carrier  WHERE id_cart_rule=%s",[row[0]])
                    cursor.execute(f"DELETE FROM ps17_cart_rule_country  WHERE id_cart_rule=%s",[row[0]])
                    cursor.execute(f"DELETE FROM ps17_cart_rule_group  WHERE id_cart_rule=%s",[row[0]])
                    cursor.execute(f"DELETE FROM ps17_cart_rule_lang  WHERE id_cart_rule=%s",[row[0]])
                    cursor.execute(f"DELETE FROM ps17_cart_rule  WHERE id_cart_rule=%s",[row[0]])
                    n+=1
