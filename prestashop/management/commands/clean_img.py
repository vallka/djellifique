from datetime import datetime, timedelta
import os
import re

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connections

db = 'presta'
id_shop = 1

import logging
logger = logging.getLogger(__name__)

cnt=0
cnt0=0
size=0

def find_product(id_image):
    global cnt0
    with connections[db].cursor() as cursor:
        sql = "select id_product from ps17_image where id_image=%s"
        cursor.execute(sql,[id_image])
        result = cursor.fetchone()
        print(result)
        if not result:
            cnt0 += 1

def doSomethingWithFile(f,fn):
    sz = os.path.getsize(f)
    global cnt
    global size


    m = re.match(r'(\d+)\.\w+$',fn) 
    if m:
        print('-------',m.group(1))
        find_product(m.group(1))
        print(f,sz)
        cnt += 1
    
    size += sz


class Command(BaseCommand):
    help = 'clean img'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        print (self.help)
        logger.info(self.help)

        today = datetime.today().date() # get a Date object
        logger.info(today)

        rootFolderPath = '/bitnami/gellifique/img/p/'

        for root, dirs, files in os.walk(rootFolderPath):
            for filename in files:
                doSomethingWithFile(os.path.join(root, filename),filename)


        print(cnt,size,cnt0)
        
        #sql="SELECT id_product,id_specific_price FROM `ps17_specific_price` WHERE id_shop=%s and `from`<=now() and `to`>=now()"
#
        #with connections[db].cursor() as cursor:
        #    cursor.execute(sql,[id_shop])
        #    result = cursor.fetchall()
#
        #    print (result)

        logger.error("DONE - %s! - %s",self.help,str(today))
