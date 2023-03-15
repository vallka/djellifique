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
MOCK_SEND = True

_post_title = ''
_post_id = 0

def my_replace(match):
    match1 = match.group(1)
    match2 = match.group(2)
    match3 = match.group(3)

    url = f"{match3}?utm_source=newsletter&utm_medium=email&utm_campaign={_post_title}&utm_id={_post_id}"
    url = urllib.parse.quote_plus(url)

    blog_url = 'https://blog.gellifique.co.uk/'

    return f'{match1}{blog_url}blog/newsletter/click/####uuid####/?path={match2}{url}'

class Command(BaseCommand):
    help = 'send newsletter'
    good_customers = []
    current_post = None

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
            print(newsletter_post[0].slug)
            print(newsletter_post[0].title)
            print(newsletter_post[0].domain)
            self.current_post = newsletter_post[0]

            html = {}
            html[1] = NewsShot.add_html_x(newsletter_post[0].slug)

            limit = 1
            if newsletter_post[0].domain==Post.Domains.EU:
                custs = self.get_customers_eu(newsletter_post[0].id,limit)
            else:
                custs = self.get_customers(newsletter_post[0].id,limit)

            if len(custs):
                dolog = True

                if newsletter_post[0].email_status==Post.EmailStatus.NONE:
                    newsletter_post[0].email_status = Post.EmailStatus.SENDING
                    newsletter_post[0].save()

                for i,c in enumerate(custs):
                    print(f"{i+1}, customer:{c[0]}:{c[1]}:{c[4]}")
                    logger.info(f"{i+1}, customer:{c[0]}:{c[1]}:{c[4]}")
                    
                    if newsletter_post[0].domain==Post.Domains.EU:
                        lang_id = c[4]
                        if not html.get(lang_id):
                            html[lang_id] = NewsShot.add_html_x(newsletter_post[0].slug,AllLanguages.getById(lang_id))
                    else:
                        lang_id = 1

                    shot = NewsShot(blog=newsletter_post[0],customer_id=c[0])
                    if self.send(c,html[lang_id],newsletter_post[0].email_subject,newsletter_post[0].title,newsletter_post[0].id,shot.uuid):
                        shot.send_dt = timezone.now()
                        shot.save() 
                        sent += 1
                    else:
                        not_sent += 1

            else:
                dolog = True
                if not MOCK_SEND and not MOCK:
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



    def encode_urls(self,html,title,id,uuid,to_email,firstname,id_customer):
        global _post_title,_post_id
        _post_title = title
        _post_id = id

        #TODO: for some reason doesn't replace links in top menu

        html = re.sub(r'(<a\s+href=")(https://www\.gellifique\.[couke.]+/)([^"]*)',my_replace,html)
        html = html.replace('####uuid####',uuid)
        html = html.replace('####email####',to_email)
        html = html.replace('<!-- Hi Firstname -->',f"Hi {firstname},")

        host = 'https://www.gellifique.co.uk' if self.current_post.domain==Post.Domains.EU else 'https://www.gellifique.eu'
        referral_url = host + '/?rid=' + str(id_customer+1000)
        
        html = html.replace('<referral_url>',referral_url)
        html = html.replace('<firstname>',firstname)

        return html


    def send(self,cust,html,subj,title,id,uuid):
        #to_email = 'vallka@vallka.com'
        id_cust = cust[0]
        to_email = cust[1]
        firstname = cust[2]
        lang = cust[4]

        html = self.encode_urls(html,title,id,str(uuid),to_email,firstname,id_cust)

        #print (html)
        if MOCK:
            print(f"MOCK: {to_email} / {lang}")
            return False
        elif MOCK_SEND:
            print(f"MOCK_SEND: {to_email} / {lang}")
            print(html)
            return False
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
                    AND c.id_customer>=3705 AND c.id_customer<=3784
                    ORDER BY c.id_customer  DESC
                    limit 0,5000
                """

                cursor.execute(sql,[blog_id,])
                rows = cursor.fetchall()

                print (f"found:{len(rows)}")
                return rows
        
        return []


    def get_customers(self,blog_id,limit):
        #extra_where = """
        #    AND c.id_customer NOT IN (
        #    SELECT id_customer FROM gellifique_new.ps17_orders o
        #    WHERE current_state IN
        #    (SELECT id_order_state FROM gellifique_new.ps17_order_state WHERE paid=1)
        #    AND DATE_ADD>='2022-11-18' AND DATE_ADD<'2022-11-29')                    
        #"""
        extra_where = ""

        if not MOCK:
            with connections['default'].cursor() as cursor:
                sql = f"""
                SELECT id_customer,email,firstname,lastname,id_lang FROM gellifique_new.ps17_customer c 
                    where active=1 and newsletter=1 and id_shop=1
                    and c.id_customer not IN (
                    select customer_id from dj.newsletter_newsshot where customer_id=c.id_customer
                    and blog_id=%s
                    )
                    {extra_where}
                    ORDER BY c.id_customer  DESC
                    limit 0,{limit}
                """
                ###    and c.email like '%%@vallka.com'

                cursor.execute(sql,[blog_id,])
                row = cursor.fetchall()
        else:
            row = [(12345,'vallka@vallka.com','Val','Kool,1')]

        return row

    def get_customers_eu(self,blog_id,limit):

            if not MOCK:
                with connections['default'].cursor() as cursor:
                    sql = f"""
                    SELECT id_customer,email,firstname,lastname,id_lang FROM gellifique_eu.ps17_customer c 
                        where active=1 and newsletter=1 and id_shop=2
                        and c.id_customer not IN (
                        select customer_id from dj.newsletter_newsshot where customer_id=c.id_customer
                        and blog_id=%s
                        )
                        ORDER BY c.id_customer  DESC
                        limit 0,{limit}
                    """
                    ###    and c.email like '%%@vallka.com'

                    cursor.execute(sql,[blog_id,])
                    row = cursor.fetchall()
            else:
                row = [(12345,'vallka@vallka.com','Val','Kool,1')]

            return row




############

class NewsShotSender:

    def send(self, *args, **options):
        sent = 0
        not_sent = 0

        # get nex newsletter_post which status is not SENT
        newsletter_post = Post.objects.filter(email=True,email_send_dt__lt=timezone.now(),email_status__in=[Post.EmailStatus.NONE,Post.EmailStatus.SENDING]).order_by('id')

        # we will send only 1st newsletter_post
        if len(newsletter_post) > 0:
            # make html from the newsletter_post content
            html = NewsShot.add_html_x(newsletter_post[0].formatted_markdown,newsletter_post[0].title,newsletter_post[0].slug,newsletter_post[0].title_color,newsletter_post[0].title_bgcolor)

            # get next 50 customers
            custs = self.get_customers(newsletter_post[0].id,50)

            if len(custs):

                if newsletter_post[0].email_status==Post.EmailStatus.NONE:
                    newsletter_post[0].email_status = Post.EmailStatus.SENDING
                    newsletter_post[0].save()

                for i,c in enumerate(custs):

                    # make personalized newsletter_post for a customer
                    shot = NewsShot(blog=newsletter_post[0],customer_id=c[0])

                    # send it!
                    if self.send(c,html,newsletter_post[0].email_subject,newsletter_post[0].title,newsletter_post[0].id,shot.uuid):
                        # save in customers's history
                        shot.send_dt = timezone.now()
                        shot.save() 
                        sent += 1
                    else:
                        not_sent += 1

            else:
                print('no more customers! - setting SENT status')

                #mark newsletter_post as fully sent
                newsletter_post[0].email_status = Post.EmailStatus.SENT
                newsletter_post[0].save()
        else:
            print('no newsletters to send!')

        print("DONE! Sent:%s, Not sent:%s" % (str(sent),str(not_sent)))
