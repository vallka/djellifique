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
RE_EMOJI = re.compile(u'([\U00002600-\U000027BF])|([\U0001f300-\U0001f64F])|([\U0001f680-\U0001f6FF])')

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

        if MOCK:
            newsletter_post = Post.objects.filter(id=253).order_by('id')    
        else:    
            newsletter_post = Post.objects.filter(email=True,draft=False,email_send_dt__lt=today,email_status__in=[Post.EmailStatus.NONE,Post.EmailStatus.SENDING]).order_by('id')


        if len(newsletter_post) > 0:
            print(newsletter_post[0].slug)
            print(newsletter_post[0].title)
            print(newsletter_post[0].domain)
            self.current_post = newsletter_post[0]

            limit = 300
            custs = self.get_customers(newsletter_post[0].id,limit,newsletter_post[0].domain)
            #custs = self.get_customers_special(newsletter_post[0].id,limit,newsletter_post[0].domain)

            if len(custs):
                dolog = True

                if newsletter_post[0].email_status==Post.EmailStatus.NONE:
                    newsletter_post[0].email_status = Post.EmailStatus.SENDING
                    newsletter_post[0].save()

                for i,c in enumerate(custs):
                    id_cust = c[0]
                    to_email = c[1]
                    firstname = c[2].strip()
                    lastname = c[3].strip()
                    lang_id = int(c[4])
                    cust_type = c[5]

                    print(f"{i+1}, customer:{c[5]}:{c[0]}:{c[1]}:{c[4]}")
                    logger.info(f"{i+1}, customer:{id_cust}:{to_email}:{firstname}:{lastname}:{lang_id}:{cust_type}")
                    
                    if newsletter_post[0].domain==Post.Domains.EU:
                        lang_id = int(c[4])
                    else:
                        lang_id = 1 ## reset to en for all

                    lang = AllLanguages.getById(lang_id)

                    shot = NewsShot(blog=newsletter_post[0],customer_id=id_cust,customer_type=cust_type)
                    html = shot.add_html_x(newsletter_post[0],lang)
                    html = shot.html_add_customer(html,newsletter_post[0].domain,customer_type=cust_type,customer_id=id_cust,customer_name=firstname,customer_email=to_email)

                    send_result = shot.send(html,[to_email],False)
                    time.sleep(0.2)


                    if send_result:
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



    def encode_urls(self,html,title,id,uuid,to_email,firstname,id_customer,cust_type):
        global _post_title,_post_id
        # for my_replace
        _post_title = 'E:' + RE_EMOJI.sub(r'',title)
        _post_id = id

        #TODO: for some reason doesn't replace links in top menu

        html = re.sub(r'(<a\s+href=")(https://www\.gellifique\.[couke.]+/)([^"]*)',my_replace,html)
        html = html.replace('####uuid####',uuid)
        html = html.replace('####email####',to_email)
        html = html.replace('<!-- Hi Firstname -->',f"Hi {firstname},")

        host = 'https://www.gellifique.co.uk' if self.current_post.domain==Post.Domains.CO_UK else 'https://www.gellifique.eu'
        if cust_type=='C':
            referral_url = host + '/?rid=' + str(id_customer+1000)
        else:
            referral_url = ''
        
        html = html.replace('<referral_url>',referral_url)
        html = html.replace('<firstname>',firstname)

        return html


    def send(self,cust,html,subj,title,id,uuid):
        #to_email = 'vallka@vallka.com'
        id_cust = cust[0]
        to_email = cust[1]
        firstname = cust[2].strip()
        lang = cust[4]
        cust_type = cust[5]

        html = self.encode_urls(html,title,id,str(uuid),to_email,firstname,id_cust,cust_type)

        #print (html)
        if MOCK:
            print(f"MOCK: {to_email} / {lang}")
            return False
        elif MOCK_SEND:
            print(f"MOCK_SEND: {to_email} / {lang}")
            #print(html)
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


    def get_customers_special(self,blog_id,limit,domain):

        if not MOCK:
            with connections['default'].cursor() as cursor:
                sql = """
                SELECT id_customer,email,firstname,lastname,id_lang,'C' AS customer_type  FROM gellifique_new.ps17_customer c 
                    where active=1 and id_shop=1
                    and c.id_customer not IN (
                    select customer_id from dj.newsletter_newsshot where customer_id=c.id_customer
                    and blog_id=%s
                    )
                    AND c.id_customer in (
                    SELECT id_customer FROM gellifique_new.ps17_address a WHERE a.postcode LIKE 'BT%%'
                    )
                    ORDER BY c.id_customer  DESC
                    limit 0,5000
                """

                cursor.execute(sql,[blog_id,])
                rows = cursor.fetchall()

                print (f"found:{len(rows)}")
                return rows
        
        return []


    def get_customers(self,blog_id,limit,domain):
        if domain==Post.Domains.EU:
            db_name = 'gellifique_eu'
            id_shop = 2
        else:
            db_name = 'gellifique_new'
            id_shop = 1



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
                    SELECT id_customer,email,firstname,lastname,id_lang,'C' AS customer_type FROM {db_name}.ps17_customer c 
                        WHERE ACTIVE=1 AND newsletter=1 AND id_shop={id_shop}
                        AND c.id_customer NOT IN (
                        SELECT customer_id FROM dj.newsletter_newsshot WHERE customer_id=c.id_customer AND customer_type='C'
                        AND blog_id=%s
                        )
                    UNION ALL                    
                    SELECT id AS id_customer,email,'' AS firstname,'' AS lastname,id_lang,'N' AS customer_type FROM {db_name}.ps17_emailsubscription e 
                        WHERE ACTIVE=1 AND id_shop={id_shop}
                        AND e.id NOT IN (
                        SELECT customer_id FROM dj.newsletter_newsshot WHERE customer_id=e.id AND customer_type='N'
                        AND blog_id=%s
                        )

                    ORDER BY customer_type DESC,id_customer  DESC     
                    limit 0,{limit}
                """


#                SELECT id_customer,email,firstname,lastname,id_lang,'C' as customer_type FROM gellifique_new.ps17_customer c 
#                    where active=1 and newsletter=1 and id_shop=1
#                    and c.id_customer not IN (
#                    select customer_id from dj.newsletter_newsshot where customer_id=c.id_customer
#                    and blog_id=%s
#                    )
#                    {extra_where}
#                    ORDER BY c.id_customer  DESC
#                    limit 0,{limit}
#                ###    and c.email like '%%@vallka.com'

                cursor.execute(sql,[blog_id,blog_id])
                row = cursor.fetchall()
        else:
            row = [(3845,'vallka@vallka.com','Val','Kool','2','C')]

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
