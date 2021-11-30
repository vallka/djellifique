from datetime import datetime, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connections

db = 'presta'
id_shop = 1
CATEGORY_OUTLET = 21
CATEGORY_SALE = 135

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'set sale'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        print (self.help)
        logger.info(self.help)

        today = datetime.today().date() # get a Date object
        logger.info(today)

        self.unsale_past_and_future()
        self.sale_present()

        print('done')
        logger.error("DONE - %s! - %s",self.help,str(today))

    def unsale_past_and_future(self):
        # specific price in past
        sql="""
SELECT id_product FROM `ps17_specific_price` sp WHERE id_shop=%s AND  `to`<NOW()
AND id_product NOT IN
(SELECT id_product FROM ps17_category_product WHERE id_category=%s)
ORDER BY id_product
        """
        result = None
        with connections[db].cursor() as cursor:
            cursor.execute(sql,[id_shop,CATEGORY_OUTLET])
            result = cursor.fetchall()

            print (len(result))

            if result and len(result):
                cursor.execute(f"insert into a_events (date_start,name) values (now(),'unsale(sp) {len(result)}')")
                for row in result:
                    print (row[0])
                    cursor.execute('update ps17_product_shop set on_sale=0 where id_shop=%s and id_product=%s',[id_shop,row[0]])
                    cursor.execute('update ps17_product set on_sale=0 where id_product=%s',[row[0]])
                    cursor.execute('delete from ps17_category_product where id_product=%s and id_category=%s',[row[0],CATEGORY_SALE])
                    cursor.execute('delete from ps17_specific_price where id_shop=%s and id_product=%s',[id_shop,row[0]])


        # category sale and no spec price now
        sql="""
SELECT id_product FROM ps17_category_product WHERE id_category=%s
AND id_product NOT IN (
SELECT id_product FROM ps17_specific_price WHERE id_shop=%s AND `from`<=NOW() AND `to`>=NOW()
)
        """
        result = None
        with connections[db].cursor() as cursor:
            cursor.execute(sql,[CATEGORY_SALE,id_shop,])
            result = cursor.fetchall()
            print (len(result))

            if result and len(result):
                cursor.execute(f"insert into a_events (date_start,name) values (now(),'unsale(cs) {len(result)}')")
                for row in result:
                    print (row[0])
                    cursor.execute('update ps17_product_shop set on_sale=0 where id_shop=%s and id_product=%s',[id_shop,row[0]])
                    cursor.execute('update ps17_product set on_sale=0 where id_product=%s',[row[0]])
                    cursor.execute('delete from ps17_category_product where id_product=%s and id_category=%s',[row[0],CATEGORY_SALE])
                    # don't touch specific price - may be in future

        # on_sale mark and no spec price now 
        sql="""
SELECT id_product FROM ps17_product_shop WHERE id_shop=%s and on_sale=1
AND id_product NOT IN (
SELECT id_product FROM ps17_specific_price WHERE id_shop=%s AND `from`<=NOW() AND `to`>=NOW()
)
        """
        result = None
        with connections[db].cursor() as cursor:
            cursor.execute(sql,[id_shop,id_shop,])
            result = cursor.fetchall()
            print (len(result))

            if result and len(result):
                cursor.execute(f"insert into a_events (date_start,name) values (now(),'unsale(os) {len(result)}')")
                for row in result:
                    print (row[0])
                    cursor.execute('update ps17_product_shop set on_sale=0 where id_shop=%s and id_product=%s',[id_shop,row[0]])
                    cursor.execute('update ps17_product set on_sale=0 where id_product=%s',[row[0]])
                    cursor.execute('delete from ps17_category_product where id_product=%s and id_category=%s',[row[0],CATEGORY_SALE])
                    # don't touch specific price - may be in future

    def sale_present(self):
        pos = 0
        with connections[db].cursor() as cursor:
            cursor.execute("select coalesce(max(position),0) from ps17_category_product WHERE id_category=%s",[CATEGORY_SALE])
            pos = cursor.fetchone()
            pos = pos[0]

        sql="""
SELECT id_product FROM `ps17_specific_price` sp WHERE id_shop=%s AND `from`<=NOW() AND `to`>=NOW()
AND id_product NOT IN
(SELECT id_product FROM ps17_category_product WHERE id_category=%s)
AND id_product NOT IN
(SELECT id_product FROM ps17_category_product WHERE id_category=%s)
ORDER BY id_product
        """
        result = None
        with connections[db].cursor() as cursor:
            cursor.execute(sql,[id_shop,CATEGORY_OUTLET,CATEGORY_SALE])
            result = cursor.fetchall()

            print (len(result))
            if result and len(result):
                cursor.execute(f"insert into a_events (date_start,name) values (now(),'sale(sP) {len(result)}')")
                for row in result:
                    pos += 1
                    print (row[0],pos)
                    cursor.execute('update ps17_product_shop set on_sale=1 where id_shop=%s and id_product=%s',[id_shop,row[0]])
                    cursor.execute('update ps17_product set on_sale=1 where id_product=%s',[row[0]])
                    cursor.execute("INSERT INTO ps17_category_product (id_category,id_product,position) values (%s,%s,%s)",[CATEGORY_SALE,row[0],pos])
