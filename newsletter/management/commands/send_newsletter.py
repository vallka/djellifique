from datetime import datetime, timedelta
import urllib
import re
import time

import pandas as pd

from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail,EmailMessage,EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from django.db import connections

from blog.models import *
from newsletter.models import *

import logging
logger = logging.getLogger(__name__)

MOCK = False
MOCK_SEND = False

_post_title = ''
_post_id = 0

def my_replace(match):
    match1 = match.group(1)
    match2 = match.group(2)
    match3 = match.group(3)

    url = f"{match3}?utm_source=newsletter&utm_medium=email&utm_campaign={_post_title}&utm_id={_post_id}"
    url = urllib.parse.quote_plus(url)

    return f'{match1}{match2}blog/newsletter/click/####uuid####/?path={url}'

class Command(BaseCommand):
    help = 'send newsletter'
    good_customers = []

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        logger.info(self.help)
        print(self.help)

        #good_customers = pd.read_csv(settings.MEDIA_ROOT + '/customer database to notify.csv',usecols=[0],names=['customer_name'],skiprows=1,skipfooter=1    )
        #print (good_customers)
        #print (good_customers['customer_name'].to_list())
        #self.good_customers = good_customers['customer_name'].to_list()

        sent = 0
        not_sent = 0
        dolog = False

        #today = datetime.today().date() # get a Date object
        today = timezone.now() # get a Date object
        #logger.info(today)

        newsletter_post = Post.objects.filter(email=True,email_send_dt__lt=today,email_status__in=[Post.EmailStatus.NONE,Post.EmailStatus.SENDING]).order_by('id')


        if len(newsletter_post) > 0:
            html = NewsShot.add_html_x(newsletter_post[0].formatted_markdown,newsletter_post[0].title,newsletter_post[0].slug,newsletter_post[0].title_color,newsletter_post[0].title_bgcolor)
            #print(self.add_html(newsletter_post[0].formatted_markdown,newsletter_post[0].title,newsletter_post[0].slug))

            custs = self.get_customers(newsletter_post[0].id)
            #custs = self.get_customers_special(newsletter_post[0].id)
            #custs = self.get_customers_eu(newsletter_post[0].id)

            if len(custs):
                dolog = True

                if newsletter_post[0].email_status==Post.EmailStatus.NONE:
                    newsletter_post[0].email_status = Post.EmailStatus.SENDING
                    newsletter_post[0].save()

                for i,c in enumerate(custs):
                    #customer_name = c[2] + ' ' + c[3]
                    #good = 1 if customer_name in self.good_customers else 0

                    #if good: 
                    #    print(f"{i+1},{c[0]},{c[1]},{customer_name},{good}")
                    #    self.good_customers.remove(customer_name)

                    logger.info(f"{i+1}, customer:{c[0]}:{c[1]}")

                    shot = NewsShot(blog=newsletter_post[0],customer_id=c[0])
                    if self.send(c,html,newsletter_post[0].email_subject,newsletter_post[0].title,newsletter_post[0].id,shot.uuid):
                        shot.send_dt = timezone.now()
                        shot.save() 
                        sent += 1
                    else:
                        not_sent += 1

            else:
                dolog = True
                print('no more customers! - setting SENT status')
                logger.info('no more customers! - setting SENT status')
                newsletter_post[0].email_status = Post.EmailStatus.SENT
                newsletter_post[0].save()
        else:
            #logger.info('no newsletters to send!')
            print('no newsletters to send!')

        print("DONE! - %s! Sent:%s, Not sent:%s" % (self.help,str(sent),str(not_sent)))
        if dolog:
            logger.error("DONE! - %s! Sent:%s, Not sent:%s",self.help,str(sent),str(not_sent))



    def encode_urls(self,html,title,id,uuid,to_email,firstname):
        global _post_title,_post_id
        _post_title = title
        _post_id = id
        html = re.sub(r'(<a\s+href=")(https://www\.gellifique\.co.uk/)([^"]*)',my_replace,html)
        html = html.replace('####uuid####',uuid)
        html = html.replace('####email####',to_email)
        html = html.replace('<!-- Hi Firstname -->',f"Hi {firstname},")
        
        return html


    def send(self,cust,html,subj,title,id,uuid):
        #to_email = 'vallka@vallka.com'
        to_email = cust[1]
        firstname = cust[2]

        html = self.encode_urls(html,title,id,str(uuid),to_email,firstname)

        #print (html)
        if MOCK:
            print(f"MOCK: {to_email}")
            return True
        elif MOCK_SEND:
            print(f"MOCK_SEND: {to_email}")
            return True
        else:
            email = EmailMultiAlternatives( subj if subj else title, title, settings.EMAIL_FROM_USER, [to_email], headers = {'X-gel-id': str(uuid)}   )
            email.attach_alternative(html, "text/html") 
            #if attachment_file: email.attach_file(attachment_file)
            
            print(f"SENDING: {to_email}...")
            send_result = email.send()
            print('send_result',send_result)
            time.sleep(0.5)
            return send_result

        return True


    def get_customers_special(self,blog_id):

        if not MOCK:
            with connections['default'].cursor() as cursor:
                sql = """
                SELECT id_customer,email,firstname,lastname,id_lang FROM gellifique_new.ps17_customer c 
                    where active=1 and id_shop=1
                    and c.id_customer not IN (
                    select customer_id from dj.newsletter_newsshot where customer_id=c.id_customer
                    and blog_id=%s
                    )
                    ORDER BY c.id_customer  DESC
                    limit 0,5000
                """

                cursor.execute(sql,[blog_id,])
                rows = cursor.fetchall()

                print (f"found:{len(rows)}")
                return rows
        
        return []


    def get_customers(self,blog_id):

        if not MOCK:
            with connections['default'].cursor() as cursor:
                sql = """
                SELECT id_customer,email,firstname,lastname,id_lang FROM gellifique_new.ps17_customer c 
                    where active=1 and newsletter=1 and id_shop=1
                    and c.id_customer not IN (
                    select customer_id from dj.newsletter_newsshot where customer_id=c.id_customer
                    and blog_id=%s
                    )
                    ORDER BY c.id_customer  DESC
                    limit 0,50
                """
                ###    and c.email like '%%@vallka.com'

                cursor.execute(sql,[blog_id,])
                row = cursor.fetchall()
        else:
            row = [(12345,'vallka@vallka.com','Val','Kool,1')]

        return row

    def get_customers_eu(self,blog_id):

            if not MOCK:
                with connections['default'].cursor() as cursor:
                    sql = """
                    SELECT id_customer,email,firstname,lastname,id_lang FROM gellifique_eu.ps17_customer c 
                        where active=1 and id_shop=2
                        and c.id_customer not IN (
                        select customer_id from dj.newsletter_newsshot where customer_id=c.id_customer
                        and blog_id=%s
                        )
                        ORDER BY c.id_customer  DESC
                        limit 0,50
                    """
                    ###    and c.email like '%%@vallka.com'

                    cursor.execute(sql,[blog_id,])
                    row = cursor.fetchall()
            else:
                row = [(12345,'vallka@vallka.com','Val','Kool,1')]

            return row

