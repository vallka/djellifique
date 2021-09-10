from django.views import generic
from rest_framework import serializers

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
        logger.error(f'get_queryset sql:{sql}')
        qs = Order.objects.using('presta').raw(sql)
        logger.error(qs)
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
        logger.error(f'get_queryset sql:{sql}')
        qs = OrderDetail.objects.using('presta').raw(sql,[self.kwargs['id_order']])
        logger.error(qs)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        sql = Order.SQL(one=True)
        logger.error(f'get_queryset in context sql:{sql}')
        qs = Order.objects.using('presta').raw(sql,[self.kwargs['id_order']])

        context['order'] = qs[0]

        return context
    
class CertListView(generic.TemplateView):    
    template_name = 'uploaded.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cert_dir = os.path.join(settings.MEDIA_ROOT,'customer-certificates',self.kwargs['email'])
        logger.error(f"CertListView:{cert_dir}")


        if os.path.isdir(cert_dir):
            logger.error(os.listdir(cert_dir))
            context['cert_dir'] = cert_dir
        
            files = []
            for f in os.listdir(cert_dir):
                url = settings.FORCE_SCRIPT_NAME + os.path.join(settings.MEDIA_URL,'customer-certificates',self.kwargs['email'],f)
                files.append({'url':url,'file':f})

            context['files'] = files

        return context
class OrderDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDetail
        fields = "__all__"

class UploadPageView(generic.TemplateView):
    template_name = 'upload.html'

import uuid
import os
from django.conf import settings

from django.views.generic import TemplateView
from django.http import HttpResponse

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def putfile(request,email):

    filename = request.GET.get('filename',str(uuid.uuid1()) + '.pdf').replace(' ','_')

    fullname = os.path.join(settings.MEDIA_ROOT,'customer-certificates',email,filename)

    os.makedirs(os.path.dirname(fullname), exist_ok=True)
    f = open(fullname,'wb')
    f.write(request.body)
    f.close()

    logger.error(settings.FORCE_SCRIPT_NAME + os.path.join(settings.MEDIA_URL,'customer-certificates',email,filename))
    
    return HttpResponse(settings.FORCE_SCRIPT_NAME + os.path.join(settings.MEDIA_URL,'customer-certificates',email,filename))

