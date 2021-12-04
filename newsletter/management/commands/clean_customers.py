from datetime import date,datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connections

db = 'presta'
id_shop = 1
CATEGORY_OUTLET = 21
CATEGORY_SALE = 135
OUTLET_PC = 0.3

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'clean customers'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        print (self.help)
        logger.info(self.help)

        today = datetime.today().date() # get a Date object
        logger.info(today)

        self.complaints()
        self.bounces()

        print('done')
        logger.error("DONE - %s! - %s",self.help,str(today))


    def complaints(self):
        print('complaints')
        sql="""
SELECT id,customer_id,send_dt FROM dj.newsletter_newsshot WHERE note='Complaint' 
AND customer_id IN (
SELECT id_customer FROM ps17_customer WHERE newsletter=1
)
ORDER BY id DESC        
"""
        result = None
        with connections[db].cursor() as cursor:
            cursor.execute(sql)
            result = cursor.fetchall()

            logger.info(f'complaints:{len(result)}')
            print (len(result))
            if result and len(result):
                print(result)
                for row in result:
                    cursor.execute('update ps17_customer set newsletter=0 where id_customer=%s',[row[1]])

    def bounces(self):
        print('bounces')
        sql="""
SELECT id,customer_id,send_dt FROM dj.newsletter_newsshot ns1 WHERE note='Bounce' 
AND send_dt>DATE_SUB(NOW(),INTERVAL 1 MONTH)
AND customer_id IN (
SELECT id_customer FROM gellifique_new.ps17_customer WHERE newsletter=1
)
AND NOT EXISTS (
SELECT * FROM dj.newsletter_newsshot ns2 WHERE ns1.customer_id=ns2.customer_id AND ns2.note='Delivery' AND ns2.id>ns1.id
)
ORDER BY id DESC
"""
        result = None
        with connections[db].cursor() as cursor:
            cursor.execute(sql)
            result = cursor.fetchall()

            print (len(result))
            logger.info(f'bounces:{len(result)}')
            if result and len(result):
                cust_no=0
                for row in result:
                    cust_no += 1
                    print(cust_no,row)
                    cursor.execute('SELECT id,note FROM dj.newsletter_newsshot WHERE note IS NOT NULL AND customer_id=%s ORDER BY id DESC',[row[1]])
                    result2 = cursor.fetchall()
                    cases = 0
                    for row2 in result2:
                        cases += 1
                        print(cases,row2)
                        if row2[1]=='Delivery': break
                        if cases>3: 
                            print('***delete***')
                            logger.info(f'deleting customer_id:{row[1]}')
                            cursor.execute('update ps17_customer set newsletter=0 where id_customer=%s',[row[1]])
                            break
