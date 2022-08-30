import uuid
import os
import json

from django.core.mail import send_mail,EmailMessage,EmailMultiAlternatives
from django.core.exceptions import ValidationError
from django.shortcuts import redirect,render
from django.views import generic

from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse,JsonResponse
from django.conf import settings
from django.db import connection,connections

import logging
logger = logging.getLogger(__name__)

from .models import *
from blog.models import *

# Create your views here.

def my_image(request):
    uuid=request.GET['uuid']

    logger.error("my_image - uuid:%s, ua:%s",uuid,request.headers['user-agent'])
    try:
        ns = NewsShot.objects.get(uuid=uuid)
        if ns.opened_dt==None:
            ns.opened_dt = timezone.now()
            ns.user_agent = request.headers['user-agent']
            ns.save()
    except NewsShot.DoesNotExist:
        logger.error("NewsShot.DoesNotExist:%s",uuid)

    except ValidationError:
        pass


    return redirect('/static/images/pixel.png')

def click_redirect(request,uuid):
    path=request.GET['path']
    print ('click_redirect',uuid,path)
    logger.error("click_redirect - uuid:%s, path:%s",uuid,path)
    try:
        ns = NewsShot.objects.get(uuid=uuid)
        if ns.clicked_dt==None:
            ns.clicked_dt = timezone.now()
            ns.clicked_qnt = 1
        else:    
            ns.clicked_qnt += 1
        ns.save()

    except NewsShot.DoesNotExist:
        logger.error("NewsShot.DoesNotExist:%s",uuid)

    return redirect('https://www.gellifique.co.uk/' + path)

class UnsubscribePageView(generic.TemplateView):
    template_name = 'prestashop/unsubscribe.html'

    def post(self, request, email, uuid):
        done = False
        try:
            ns = NewsShot.objects.get(uuid=uuid)
            print(ns.customer_id,ns.note)
            if not 'unsubscribed' in ns.note:
                db = 'presta'

                sql="update ps17_customer set newsletter=0 where newsletter=1 and id_customer=%s and email=%s"
                #sql="select * from ps17_customer where newsletter=1 and id_customer=%s and email=%s"
                with connections[db].cursor() as cursor:
                    cursor.execute(sql,[ns.customer_id,email])
                    #result = cursor.fetchall()
                    #print(result)

                ns.note = ns.note + '/unsubscribed'
                ns.save()
                done = True

        except Exception as e:
            logger.error("NewsShot.DoesNotExist:%s or Exception:%s",uuid,e)
            print("NewsShot.DoesNotExist:%s or Exception:%s" % (uuid,e))
        return render(request, self.template_name, {'email':email,'uuid':uuid,'done':done})

@csrf_exempt
@require_POST
def notification(request):
    #logger.error("notification:%s",request.body)

    message_id = ''
    note = json.loads(request.body)

    if note.get("Type")=="SubscriptionConfirmation":
        logger.error("SubscriptionConfirmation:SubscribeURL:%s",note.get("SubscribeURL"))

    
    if note.get('mail') and note["mail"].get("headers"):
        for h in note["mail"]["headers"]:
            if h['name']=='X-gel-id':
                message_id = h['value']
                break


        if message_id:
            try:
                shot = NewsShot.objects.get(uuid=message_id)
                if shot:
                    shot.note = note["notificationType"]
                    if note["notificationType"]=='Delivery':
                        shot.received_dt = timezone.now()
                    shot.save()

            except NewsShot.DoesNotExist:
                pass

            except ValidationError:
                pass


        #logger.error("notification!!!:%s,%s,%s",note["notificationType"],note["mail"]["destination"][0],message_id)

    return HttpResponse('ok')

@require_POST
def sendtest(request,slug):

    print('sendtest:',slug)
    print(request.user.email)
    logger.info("sendtest:%s",slug)

    post = Post.objects.get(slug=slug)
    #to_emails = [request.user.email]
    to_emails = ['info@gellifique.co.uk','vallka@vallka.com','larisa.eccles@btinternet.com']

    html = NewsShot.add_html_x(post.formatted_markdown,post.title,post.slug,post.title_color,post.title_bgcolor)
    html = html.replace('<!-- Hi Firstname -->',"Hi Firstname,")

    email = EmailMultiAlternatives( '[TEST NEWSLETTER] ' + post.email_subject if post.email_subject else post.title, post.title, settings.EMAIL_FROM_USER, to_emails, headers = {'X-gel-id': f'xxx-{to_emails[0]}-xxx'}  )
    email.attach_alternative(html, "text/html") 
    #if attachment_file: email.attach_file(attachment_file)
    
    send_result = email.send()
    message_id = email.extra_headers.get('X-gel-id','-')
    print('send_result',send_result,message_id)
    logger.info(email.extra_headers)
    logger.error("send_result:%s:%s",send_result,message_id)


    return JsonResponse({'result':'ok'})    

@require_POST
def stats(request,slug):

    post = Post.objects.get(slug=slug)

    print('stats:',slug,post.id)
    logger.info("stats:%s",slug)

    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(send_dt),COUNT(received_dt),COUNT(opened_dt),COUNT(clicked_dt), " + 
            "(SELECT COUNT(id) FROM newsletter_newsshot WHERE blog_id=ns.blog_id AND note = 'Bounce') bounces, " + 
            "(SELECT COUNT(id) FROM newsletter_newsshot WHERE blog_id=ns.blog_id AND note LIKE '%%unsubscribed%%') unsubscribed, " + 
            "(SELECT COUNT(id) FROM newsletter_newsshot WHERE blog_id=ns.blog_id AND note = 'Complaint') complaints " + 
            "FROM newsletter_newsshot ns WHERE blog_id=%s", [post.id])

        row = cursor.fetchone()
        return JsonResponse({'result':'ok','data':row})        

    return JsonResponse({'result':'error'})        