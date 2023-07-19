import re
import requests
from datetime import date,datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connections

db = 'presta'
id_shop = 1
STATUS_SHIPPED = 4
STATUS_DELIVERED = 5
STATUS_READY_DPD = 20
STATUS_READY_DHL = 21
STATUS_READY_RM = 40



import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'set delivered'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        global db,id_shop
        print (self.help)
        logger.info(self.help)

        today = datetime.today().date() # get a Date object
        logger.info(today)

        sql="""
SELECT id_order,current_state,shipping_number FROM `ps17_orders` WHERE id_shop=%s AND current_state=%s and shipping_number is not null and shipping_number!=''
        """
        result = None
        with connections[db].cursor() as cursor:
            cursor.execute(sql,[id_shop,STATUS_SHIPPED])
            result = cursor.fetchall()

            print (len(result))
            for o in result:
                id = o[0]
                sn = o[2]
                link = ''
                if re.search('^\d{10}\&\w+$',sn):
                    nua = sn.replace('&','&postcode=')
                    link='https://apis.track.dpdlocal.co.uk/v1/track?parcel=' + nua
                elif re.search('^[A-Z]{2}\d+GB$',sn):
                    link='https://www.royalmail.com/track-your-item#/tracking-results/'+sn
                elif re.search('^\d{10}$',sn):
                    link='https://mydhl.express.dhl/gb/en/tracking.html#/results?id=' + sn

                print(id,sn,link)    
                if link:
                    page = requests.get(link)
                    print (page.text)
                    break

        print('done')
        logger.error("DONE - %s! - %s",self.help,str(today))

