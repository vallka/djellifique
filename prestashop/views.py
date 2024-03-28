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
        qs = Order.objects.using('presta').raw(sql)
        #logger.error(qs)
        return qs

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
        qs = OrderDetail.objects.using('presta').raw(sql,[self.kwargs['id_order']])
        #logger.error(qs)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        sql = Order.SQL(one=True)
        #logger.error(f'get_queryset in context sql:{sql}')
        qs = Order.objects.using('presta').raw(sql,[self.kwargs['id_order']])

        context['order'] = qs[0]

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
        context['category'] = PrintCategory(self.kwargs['id_category'])
        return context
    
class PrintCategoriesView(generic.TemplateView):
    template_name = 'prestashop/printcategories.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pages'] = []
        context['pages'].append({'category': PrintCategory(169)})
        context['pages'].append({'category': PrintCategory(171)})
        context['pages'].append({'category': PrintCategory(170)})
        context['pages'].append({'category': PrintCategory(172)})

        return context
    

class PrintColoursView(generic.TemplateView):
    template_name = 'prestashop/printcolours.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = PrintCategory(self.kwargs['id_category'])
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
        print('get')
        r = super().get(request, *args, **kwargs)
        r.headers['Content-Security-Policy'] = "frame-ancestors 'self' *.gellifique.co.uk *.gellifique.eu; default-src 'self' 'unsafe-inline' *"
        return r
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['id_category'] = self.kwargs.get('id_category',170)
        context['category'] = PrintCategory(context['id_category'])
        
        context['pages'] = []

        context['pages'].append({'products':context['category'].products,})

        context['no_header'] = True
        context['no_footer'] = True
        context['no_gtag'] = True

        context['HTTP_REFERER'] = self.request.META.get('HTTP_REFERER')

      
        return context        
    
@require_POST
def save_sort(request):
    global db

    #db = 'presta'
    #if obj['shop_context']=='eu':
    #    db = 'presta_eu'
    #    id_shop = 2

    print('save_post')
    data = request.POST
    print(data['id_category'])
    ids = json.loads(data['sort'])
    print(ids)

    with connections[db].cursor() as cursor:
        pos = 1
        for id in ids:
            print('id_product=',id)
            sql = "update ps17_category_product set position=%s where id_category=%s and id_product=%s"
            cursor.execute(sql,[pos,data['id_category'],id])
            pos += 1
    
    r = {'result':'ok'} 

    return JsonResponse(r)    
