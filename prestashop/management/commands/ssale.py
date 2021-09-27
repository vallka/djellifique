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

        sql="SELECT id_product,id_specific_price FROM `ps17_specific_price` WHERE id_shop=%s and `from`<=now() and `to`>=now()"

        with connections[db].cursor() as cursor:
            cursor.execute(sql,[id_shop])
            result = cursor.fetchall()

            print (result)

        logger.error("DONE - %s! - %s",self.help,str(today))
