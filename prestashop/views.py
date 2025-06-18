import uuid
import os
import json
from django.conf import settings

from django.views.generic import TemplateView
from django.http import JsonResponse,HttpResponseRedirect,HttpResponse

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from django.views import generic
from rest_framework import serializers
from django.db import connections
from icecream import ic

db = 'presta'


# Create your views here.
from .models import *

import logging
logger = logging.getLogger(__name__)

class ProductListView(generic.ListView):
    model = Ps17Product

    def get_queryset(self):
        return Ps17Product.objects.all().using('presta').order_by('-id_product')[:50]

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ps17Product
        fields = '__all__'

class OrderListView(generic.ListView):

    def get_queryset(self):
        """
        """
        sql = Order.SQL()
        #logger.error(f'get_queryset sql:{sql}')

        if '127.0.0.1' in self.request.META['HTTP_HOST'] or 'gellifique.eu' in self.request.META['HTTP_HOST']:
            db = 'presta_eu'
        else:
            db = 'presta'

        qs = Order.objects.using(db).raw(sql)
        #logger.error(qs)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        sql = """
            SELECT name,COUNT(id_order) o_qnt FROM ps17_orders o 
            JOIN ps17_order_state_lang sl ON sl.id_order_state=o.current_state AND sl.id_lang=1 
            WHERE
            current_state  IN (2,3,9,11,12,17,20,21,22,23,24,25,26,27,31,39,40)
            AND o.date_add>=DATE_SUB(NOW(),INTERVAL 1 MONTH)
            GROUP BY name
            ORDER BY name
        """

        if '127.0.0.1' in self.request.META['HTTP_HOST'] or 'gellifique.eu' in self.request.META['HTTP_HOST']:
            db = 'presta_eu'
        else:
            db = 'presta'

        with connections[db].cursor() as cursor:
            cursor.execute(sql)
            result = cursor.fetchall()
        context['o_qnt'] = result

        #print(result)

        return context


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"

class OrderDetailListView(generic.ListView):

    def get_queryset(self):
        """
        """
        sql = OrderDetail.SQL()
        #logger.error(f'get_queryset sql:{sql}')
        if '127.0.0.1' in self.request.META['HTTP_HOST'] or 'gellifique.eu' in self.request.META['HTTP_HOST']:
            db = 'presta_eu'
        else:
            db = 'presta'
        qs = OrderDetail.objects.using(db).raw(sql,[self.kwargs['id_order']])
        #logger.error(qs)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        sql = Order.SQL(one=True)
        #logger.error(f'get_queryset in context sql:{sql}')
        if '127.0.0.1' in self.request.META['HTTP_HOST'] or 'gellifique.eu' in self.request.META['HTTP_HOST']:
            db = 'presta_eu'
            img_base = 'https://ik.imagekit.io/gellifiqueeu/tr:w-600,h-600/'
        else:
            db = 'presta'
            img_base = 'https://ik.imagekit.io/bbwr0ylxa/tr:w-600,h-600/'
        #print(sql,self.kwargs['id_order'])
        qs = Order.objects.using(db).raw(sql,[self.kwargs['id_order']])

        total_qnt = 0
        for p in context['orderdetail_list']:
            p.image = img_base + str(p.id_image) + '/img.jpg'
            if p.product_type!='pack':
                total_qnt += int(p.product_quantity or 0)
                if '//' in (p.product_name or ''):
                    p.product_type='pack_content'

        context['order'] = qs[0]
        context['total_qnt'] = total_qnt

        return context

class OrderDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDetail
        fields = "__all__"

class CertListView(generic.TemplateView):    
    template_name = 'prestashop/uploaded.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cert_dir = os.path.join(settings.MEDIA_ROOT,'customer-certificates',self.kwargs['email'])
        #logger.error(f"CertListView:{cert_dir}")


        if os.path.isdir(cert_dir):
            #logger.error(os.listdir(cert_dir))
            context['cert_dir'] = cert_dir
        
            files = []
            for f in os.listdir(cert_dir):
                url = str(settings.FORCE_SCRIPT_NAME or '') + os.path.join(settings.MEDIA_URL,'customer-certificates',self.kwargs['email'],f)
                #url = '' + os.path.join(settings.MEDIA_URL,'customer-certificates',self.kwargs['email'],f)
                files.append({'url':url,'file':f})

            context['files'] = files

        return context
class UploadPageView(generic.TemplateView):
    template_name = 'prestashop/upload.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customer_cert_id'] = self.request.COOKIES.get('customer_cert_id')

        if self.kwargs['email']==context['customer_cert_id']:
            cert_dir = os.path.join(settings.MEDIA_ROOT,'customer-certificates',self.kwargs['email'])

            if os.path.isdir(cert_dir):
                #logger.error(os.listdir(cert_dir))
                context['cert_dir'] = cert_dir
            
                files = []
                for f in os.listdir(cert_dir):
                    url = str(settings.FORCE_SCRIPT_NAME or '') + os.path.join(settings.MEDIA_URL,'customer-certificates',self.kwargs['email'],f)
                    #url = '' + os.path.join(settings.MEDIA_URL,'customer-certificates',self.kwargs['email'],f)
                    files.append({'url':url,'file':f})

                context['files'] = files

        return context



@csrf_exempt
def putfile(request,email):

    filename = request.GET.get('filename',str(uuid.uuid1()) + '.pdf').replace(' ','_')

    fullname = os.path.join(settings.MEDIA_ROOT,'customer-certificates',email,filename)

    os.makedirs(os.path.dirname(fullname), exist_ok=True)
    f = open(fullname,'wb')
    f.write(request.body)
    f.close()

    logger.error(str(settings.FORCE_SCRIPT_NAME or '') + os.path.join(settings.MEDIA_URL,'customer-certificates',email,filename))
    
    return HttpResponse(str(settings.FORCE_SCRIPT_NAME or '') + os.path.join(settings.MEDIA_URL,'customer-certificates',email,filename))


class PrintCategoryView(generic.TemplateView):
    template_name = 'prestashop/printcategory.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = PrintCategory(self.kwargs['id_category'],self.request.META['HTTP_HOST'])
        return context
    
class PrintCategoriesView(generic.TemplateView):
    template_name = 'prestashop/printcategories.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pages'] = []
        context['pages'].append({'category': PrintCategory(169,self.request.META['HTTP_HOST'])})
        context['pages'].append({'category': PrintCategory(171,self.request.META['HTTP_HOST'])})
        context['pages'].append({'category': PrintCategory(170,self.request.META['HTTP_HOST'])})
        context['pages'].append({'category': PrintCategory(172,self.request.META['HTTP_HOST'])})

        return context
    

class PrintColoursView(generic.TemplateView):
    template_name = 'prestashop/printcolours.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = PrintCategory(self.kwargs['id_category'],self.request.META['HTTP_HOST'])
        context['id_category'] = self.kwargs['id_category']
        
        context['pages'] = []

        #context['pages'].append({'products':context['category'].products[0:60],})
        #context['pages'].append({'products':context['category'].products[60:120],})
        #context['pages'].append({'products':context['category'].products[120:180]})
        context['pages'].append({'products':context['category'].products[0:50],})
        context['pages'].append({'products':context['category'].products[50:100],})
        context['pages'].append({'products':context['category'].products[100:150]})
        
        return context    
    
class ColourChartView(generic.TemplateView):
    template_name = 'prestashop/viewcolours.html'

    def get(self, request, *args, **kwargs):
        #print('get')
        r = super().get(request, *args, **kwargs)
        r.headers['Content-Security-Policy'] = "frame-ancestors 'self' *.gellifique.co.uk *.gellifique.eu; default-src 'self' 'unsafe-inline' *"
        #r.headers['Referrer-Policy'] = "unsafe-url"
        return r
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['id_category'] = self.kwargs.get('id_category',170)
        context['category'] = PrintCategory(context['id_category'],self.request.META['HTTP_HOST'])
        
        context['pages'] = []

        context['pages'].append({'products':context['category'].products,})

        context['no_header'] = True
        context['no_footer'] = True
        context['no_gtag'] = True

        context['HTTP_REFERER'] = self.request.META.get('HTTP_REFERER')
        
        if self.request.GET.get('a'):
            context['can_save'] = 1


        #ic(self.request.META)

      
        return context        
    
@require_POST
def save_sort(request):
    global db

    host = request.META['HTTP_HOST']

    if '127.0.0.1' in host or 'gellifique.eu' in host:
        db = 'presta_eu'
        id_shop = 2
    else:
        db = 'presta'
        id_shop = 1

    #print('save_post')
    data = request.POST
    #print(data['id_category'])
    ids = json.loads(data['sort'])
    ids_commaed = ','.join(ids)

    with connections[db].cursor() as cursor:
        sql = f"update ps17_category_product set position=%s where id_category=%s and id_product not in ({ids_commaed})"
        #print(sql)
        pos = 9999
        cursor.execute(sql,[pos,data['id_category']])
        pos = 1
        for id in ids:
            #print('id_product=',id)
            sql = "update ps17_category_product set position=%s where id_category=%s and id_product=%s"
            cursor.execute(sql,[pos,data['id_category'],id])
            pos += 1
    
    r = {'result':'ok'} 

    return JsonResponse(r)    
