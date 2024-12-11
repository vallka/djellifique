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
            errorAlert = ErrorAlert.objects.filter(domain=db,).latest('id')
            print(errorAlert)
            last_dt = errorAlert.error_dt
        except ErrorAlert.DoesNotExist:
            last_dt = '2024-01-01 00:00:00'

        sql=["""
SELECT id_log,message,object_type,object_id,date_add from ps17_log where date_add>%s and 
(
    message like '%%Order cannot be created%%' or
    message like '%%onCaptureSuccess.LOST CONTENT%%'
)
ORDER BY id_log
        ""","""
SELECT * FROM ps17_stripe_event e1 WHERE STATUS='CREATED' 
AND date_add>%s
AND date_add<DATE_SUB(NOW(), INTERVAL 5 MINUTE) 
AND NOT EXISTS
(SELECT id_payment_intent FROM ps17_stripe_event e2 WHERE STATUS='AUTHORIZED' AND e1.id_payment_intent=e2.id_payment_intent)
"""]

        result = None
        with connections[db].cursor() as cursor:
            cursor.execute(sql[0],[last_dt])
            result = cursor.fetchall()

            n=1
            print (len(result))
            
            error_type=''
            text = ''
            new_dt = None
            if result and len(result):
                error_type='log'
                for row in result:
                    print(n,row[0],row[1],row[2],row[3],row[4])
                    text += f"{row[0]} {row[4]} {row[1]} {row[2]} {row[3]}\n"
                    new_dt = row[4]
                    n+=1

            print(sql[1],last_dt)
            cursor.execute(sql[1],[last_dt])
            result2 = cursor.fetchall()

            pi = None
            if result2 and len(result2):
                error_type+='stripe'
                for row in result2:
                    print(n,row[0],row[1],row[2],row[3],row[4])
                    text += f"{row[0]} {row[1]} {row[2]} {row[3]}\n"
                    new_dt = row[3]
                    pi = row[1]
                    n+=1
                    break

            if pi:
                sql2 = """
            select msg,date_add from ps17_stripe_official_processlogger
            where name='webhook - constructEvent'
            and msg like %s
            and date_add>%s
            order by 1 desc
"""
                cursor.execute(sql2,[f"%{pi}%",last_dt])
                result3 = cursor.fetchall()

                #print(result3[0])
                text += result3[0][0]


            if text:
                #print (text)
                timezone = pytz.timezone('UTC')
                new_dt = timezone.localize(new_dt)
                print (new_dt)
                errorAlert = ErrorAlert(domain=db,error_type=error_type,text=text,error_dt=new_dt)
                errorAlert.save()

                text = f"Log: {db}\n\n{text}"
                #email = EmailMessage(subject='*** Error Alert from Gellifique ***',body=text,to=['vallka@vallka.com'],from_email='admin@gellifique.co.uk')
                #email.send()

