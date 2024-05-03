import pytz
from datetime import date,datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connections
from django.core.mail import send_mail,EmailMessage,EmailMultiAlternatives

from prestashop.models import ErrorAlert

id_shop = 1

import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'error alert'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        print (self.help)
        logger.info(self.help)

        today = datetime.today() # get a Date object
        logger.info(today)

        self.get_log('presta')
        self.get_log('presta_eu')

        print('done:'+self.help,str(today))
        logger.error("DONE - %s! - %s",self.help,str(today))

    def get_log(self,db='presta'):
        print('get_log')
        try:
            errorAlert = ErrorAlert.objects.filter(domain=db,error_type='log').latest('id')
            print(errorAlert)
            last_dt = errorAlert.error_dt
        except ErrorAlert.DoesNotExist:
            last_dt = '2024-01-01 00:00:00'

        sql="""
SELECT id_log,message,object_type,object_id,date_add from ps17_log where date_add>%s and message like '%%Order cannot be created%%' ORDER BY id_log
        """

        result = None
        with connections[db].cursor() as cursor:
            cursor.execute(sql,[last_dt])
            result = cursor.fetchall()

            n=1
            print (len(result))

            text = ''
            last_dt = None
            if result and len(result):
                for row in result:
                    print(n,row[0],row[1],row[2],row[3],row[4])
                    text += f"{row[0]} {row[4]} {row[1]} {row[2]} {row[3]}\n"
                    last_dt = row[4]
                    n+=1

            if text:
                print (text)
                timezone = pytz.timezone('UTC')
                last_dt = timezone.localize(last_dt)
                print (last_dt)
                errorAlert = ErrorAlert(domain=db,error_type='log',text=text,error_dt=last_dt)
                errorAlert.save()

                text = f"Log: {db}\n\n{text}"
                email = EmailMessage(subject='*** Error Alert from Gellifique ***',body=text,to=['vallka@vallka.com'],from_email='admin@gellifique.co.uk')
                email.send()

