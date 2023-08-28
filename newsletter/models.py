import uuid
import requests
import re
import requests
import urllib
from bs4 import BeautifulSoup
from django.core.mail import send_mail,EmailMessage,EmailMultiAlternatives
from django.conf import settings

import css_inline

from django.db import models

from blog.models import *

# Create your models here.
class NewsShot(models.Model):
    class Meta:
        ordering = ['-id']

    uuid = models.UUIDField(db_index=True, default=uuid.uuid1, editable=True,unique=True)
    blog = models.ForeignKey(Post,on_delete=models.CASCADE,)
    customer_id = models.IntegerField(db_index=True)
    customer_type = models.CharField(max_length=1,default='C')  # (C)ustomer or (N)ewletter
    send_dt = models.DateTimeField(blank=True, null=True)
    received_dt = models.DateTimeField(blank=True, null=True)
    opened_dt = models.DateTimeField(blank=True, null=True)
    clicked_dt = models.DateTimeField(blank=True, null=True)
    clicked_qnt = models.IntegerField(blank=True, null=True)
    note = models.CharField(blank=True, null=True, max_length=25)
    user_agent = models.CharField(blank=True, null=True, max_length=500)

    html_cache = {}

    @staticmethod
    def modify_urls(html, utm_tags):
        soup = BeautifulSoup(html, 'html.parser')
        blog_url = 'https://blog.gellifique.co.uk'
        
        for tag in soup.find_all('a', href=True):  # Find all anchor tags with href attribute
            if (tag['href'].startswith('https://www.gellifique.') 
                    or tag['href'].startswith('https://blog.gellifique.')) and not '/unsubscribe/' in tag['href']:
                if '?' in tag['href']:
                    tag['href'] += f'&{utm_tags}'
                else:
                    tag['href'] += f'?{utm_tags}'

                url = urllib.parse.quote_plus(tag['href'])
                tag['href'] = f'{blog_url}/blog/newsletter/click/####uuid####/?path={url}'
        
        return str(soup)

    def add_html_x(self,post,lang=None,host=None):

        if lang and lang!='en': 
            lang1 = lang + '/'
        else:
            lang1 = ''
            lang = 'en'

        if NewsShot.html_cache.get(post.slug+':'+lang):
            print ('cache hit')
            return NewsShot.html_cache.get(post.slug+':'+lang)    

        if not host: host = "https://blog.gellifique.co.uk"
        url = f"{host}/{lang1}blog/newsletter/{post.slug}"

        print ('request '+url)

        html = requests.get(url)
        if html.status_code==200:
            html = html.text

            # replace '/en/' in html with 'f"/{lang}/"'
            if lang and lang!='en':
                html = re.sub(r'(https://www\.gellifique\.co\.uk/)(en)/',f"\g<1>{lang}/",html)
                html = re.sub(r'(https://www\.gellifique\.eu/)(en)/',f"\g<1>{lang}/",html)

            campaign = 'E:' + post.slug
            utm_tags = f"utm_source=newsletter&utm_medium=email&utm_campaign={campaign}&utm_id={post.id}"
            html = NewsShot.modify_urls(html,utm_tags)

            try:
                inliner = css_inline.CSSInliner(remove_style_tags=True)
                html = inliner.inline(html)
            except:
                inliner = css_inline.CSSInliner()
                html = inliner.inline(html)

            NewsShot.html_cache[post.slug+':'+lang] = html   

        return html


    def html_add_customer(self,html,domain,customer_type,customer_id,customer_name,customer_email):
        if html:
            html = html.replace('####uuid####',str(self.uuid))
            html = html.replace('####email####',customer_email)
            html = html.replace('<!-- Hi Firstname -->',f"Hi {customer_name},")
            html = html.replace('<firstname>',customer_name)

            host = 'https://www.gellifique.co.uk' if domain==Post.Domains.CO_UK else 'https://www.gellifique.eu'
            if customer_type=='C':
                referral_url = host + '/?rid=' + str(customer_id+1000)
            else:
                referral_url = ''
            
            html = html.replace('<referral_url>',referral_url)
        return html

    def send(self,html,to_emails,test=True):
        r=re.search('<title>(.*?)</title>',html,flags=re.S) # subject sent to us in <title> tag
        subject = r.group(1)
        if test: subject = f'[TEST] {subject}'
        text = subject

        email = EmailMultiAlternatives( subject, text, settings.EMAIL_FROM_USER, to_emails, headers = {'X-gel-id': str(self.uuid)}  )
        email.attach_alternative(html, "text/html") 
        
        send_result = email.send()
        if send_result and not test:
            self.send_dt = timezone.now()
            self.save() 

        return send_result


    @staticmethod
    def get_trustpilot():
        tp = requests.get('https://uk.trustpilot.com/review/gellifique.co.uk?utm_medium=trustbox&utm_source=MicroReviewCount')
        soup = BeautifulSoup(tp.text, 'html.parser')
        p=soup.find('p',attrs={'data-reviews-count-typography':'true'})
        if p:
            return re.sub('\D?','',p.text)
        return 257
