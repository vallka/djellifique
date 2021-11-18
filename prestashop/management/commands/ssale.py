from datetime import datetime, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connections

db = 'presta'
id_shop = 1

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

        self.unsale_past()

        print('done')
        logger.error("DONE - %s! - %s",self.help,str(today))

    def unsale_past(self):
        sql="""
SELECT id_product FROM `ps17_specific_price` sp WHERE id_shop=%s AND  `to`<NOW()
AND id_product NOT IN
(SELECT id_product FROM ps17_category_product WHERE id_category=21)
ORDER BY id_product
        """

        with connections[db].cursor() as cursor:
            cursor.execute(sql,[id_shop])
            result = cursor.fetchall()

            print (result)



