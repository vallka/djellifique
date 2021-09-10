import json
import pprint
import requests
import base64
import re

from rest_framework import viewsets,generics
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated 
from rest_framework.response import Response
from rest_framework.exceptions import ParseError
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view

from drf_yasg.utils import swagger_auto_schema
from django.conf import settings
from django.db import connections

from .models import *
from .views import *

import logging
logger = logging.getLogger(__name__)

db = 'presta'

class OrderList(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)     
    serializer_class = OrderSerializer

    @swagger_auto_schema(operation_description="Orders")
    def get(self, request, *args, **kwargs):

        sql = Order.SQL()
        logger.error(f'get sql:{sql}')
        qs = Order.objects.using(db).raw(sql)
       
        serializer = self.get_serializer(qs, many=True)
    
        return Response(serializer.data)                

class OrderDetailList(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)     
    serializer_class = OrderDetailSerializer

    @swagger_auto_schema(operation_description="Order Detail")
    def get(self, request, *args, **kwargs):

        sql = OrderDetail.SQL()
        logger.error(f'get sql:{sql}')
        qs = OrderDetail.objects.using(db).raw(sql,[kwargs['id_order']])
       
        serializer = self.get_serializer(qs, many=True)
    
        return Response(serializer.data)                


class ProductList(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)     
    serializer_class = ProductSerializer

    @swagger_auto_schema(operation_description="Products by id (comma separated)")
    def get(self, request, *args, **kwargs):
        ids = kwargs.get('ids', '')

        queryset = Ps17Product.objects.using(db).filter(id_product__in=kwargs.get('ids', '').split(','))

        logger.info(f'ProductList:{ids}')
        #logger.error(queryset)

        serializer = self.get_serializer(queryset, many=True)
    
        return Response(serializer.data)                

class UpdateOrderStatus(APIView):
    permission_classes = (IsAuthenticated,)     
    parser_class = (JSONParser,)

    @swagger_auto_schema(operation_description="Update order status",)
    def post(self, request, format=None):
        obj = request.data
        logger.info(f"UpdateOrderStatus:{obj['id_order']} | {obj['id_status']}")

        with connections[db].cursor() as cursor:
            cursor.execute("select current_state from ps17_orders where id_order=%s",[obj['id_order']])
            state = cursor.fetchone()[0]

            cursor.execute("update ps17_orders set current_state=%s where id_order=%s",[obj['id_status'],obj['id_order']])
            cursor.execute("insert into ps17_order_history (id_employee,id_order,id_order_state,date_add) values (%s,%s,%s,now())", [0,obj['id_order'],obj['id_status']])

            if state!=3: #processing in progress
                cursor.execute("update ps17_orders set current_state=%s where id_order=%s",[state,obj['id_order']])
                cursor.execute("insert into ps17_order_history (id_employee,id_order,id_order_state,date_add) values (%s,%s,%s,now())", [0,obj['id_order'],state])

        return Response({'success':1,'req':obj,'state':state})                

class UpdateProduct(APIView):
    permission_classes = (IsAuthenticated,)     
    parser_class = (JSONParser,)

    @swagger_auto_schema(operation_description="Update product",)
    def post(self, request, format=None):

        obj = request.data
        logger.info(f"UpdateProduct:{obj['ids']} | {obj['what']} | {obj['search']} | {obj['replace']} | {obj['shop_context']}")
        id_shop = None
        ids_shop = None
        if obj['shop_context'] and obj['shop_context'][0]=='s':
            id_shop = obj['shop_context'][2:]
        elif obj['shop_context'] and obj['shop_context'][0]=='g':
            pass
        ids_shop = 'some group'
            # TODO: next time:)


        n = 0
        n_updated = 0
        if obj['ids'] and obj['what']:
            ids = obj['ids'].split(',')

            if obj['search']:
                if obj['what']=='reference':
                    queryset = Ps17Product.objects.using(db).filter(id_product__in=ids)
                    l = len(queryset)
                    logger.info(f'found:{l}')
                    for p in queryset:
                        n += 1
                        new_reference = re.sub(obj['search'],obj['replace'],p.reference)
                        logger.info(f"{n} {p.id_product}: {p.reference}=>{new_reference}")
                        if p.reference!=new_reference:
                            p.reference=new_reference
                            p.save()
                            n_updated += 1
                            logger.info(f'saved:{p.id_product}')

                if obj['what'][0:4]=='name':
                    id_lang = int(obj['what'][5:])
                    logger.info(f'id_lang:{id_lang}')
                    if id_shop:
                        queryset = Ps17ProductLang.objects.using(db).filter(id_product__in=ids,id_lang=id_lang,id_shop=id_shop)
                    else:
                        queryset = Ps17ProductLang.objects.using(db).filter(id_product__in=ids,id_lang=id_lang)
                    l = len(queryset)
                    logger.info(f'found:{l}')
                    for p in queryset:
                        n += 1
                        new_name = re.sub(obj['search'],obj['replace'],p.name)
                        logger.info(f"{n} {p.id_product}: {p.name}=>{new_name}")
                        if p.name!=new_name:
                            p.name=new_name
                            
                            #p.save()
                            # DOSN'T WORK AS ps_product_lang uses composite pk!

                            logger.info("update ps17_product_lang set name=%s where id_product=%s and id_lang=%s and id_shop=%s")
                            logger.info(f"pars:{new_name},{p.id_product},{p.id_lang},{p.id_shop}")


                            with connections[db].cursor() as cursor:
                                cursor.execute("update ps17_product_lang set name=%s where id_product=%s and id_lang=%s and id_shop=%s",
                                    [new_name,p.id_product,p.id_lang,p.id_shop])

                            n_updated += 1
                            logger.info(f'saved:{p.id_product},{p.id_lang},{p.id_shop}')

                if obj['what'][0:7]=='summary':
                    id_lang = int(obj['what'][8:])
                    logger.info(f'id_lang:{id_lang}')
                    if id_shop:
                        queryset = Ps17ProductLang.objects.using(db).filter(id_product__in=ids,id_lang=id_lang,id_shop=id_shop)
                    else:
                        queryset = Ps17ProductLang.objects.using(db).filter(id_product__in=ids,id_lang=id_lang)
                    l = len(queryset)
                    logger.info(f'found:{l}')
                    for p in queryset:
                        n += 1
                        new_description_short = re.sub(obj['search'],obj['replace'],p.description_short,flags=re.DOTALL)
                        logger.info(f"{n} {p.id_product}: {p.description_short}=>{new_description_short}")
                        if p.description_short!=new_description_short:
                            p.description_short=new_description_short
                            
                            #p.save()
                            # DOSN'T WORK AS ps_product_lang uses composite pk!

                            logger.info("update ps17_product_lang set description_short=%s where id_product=%s and id_lang=%s and is_shop=%s")
                            logger.info(f"pars:{new_description_short},{p.id_product},{p.id_lang},{p.id_shop}")


                            with connections[db].cursor() as cursor:
                                cursor.execute("update ps17_product_lang set description_short=%s where id_product=%s and id_lang=%s and id_shop=%s",
                                    [new_description_short,p.id_product,p.id_lang,p.id_shop])

                            n_updated += 1
                            logger.info(f'saved:{p.id_product},{p.id_lang},{p.id_shop}')

                if obj['what'][0:11]=='description':
                    id_lang = int(obj['what'][12:])
                    logger.info(f'id_lang:{id_lang}')
                    if id_shop:
                        queryset = Ps17ProductLang.objects.using(db).filter(id_product__in=ids,id_lang=id_lang,id_shop=id_shop,)
                    else:
                        queryset = Ps17ProductLang.objects.using(db).filter(id_product__in=ids,id_lang=id_lang,)
                    l = len(queryset)
                    logger.info(f'found:{l}')
                    for p in queryset:
                        n += 1
                        new_description = re.sub(obj['search'],obj['replace'],p.description,flags=re.DOTALL)
                        logger.info(f"{n} {p.id_product}: {p.description}=>{new_description}")
                        if p.description!=new_description:
                            p.description=new_description
                            
                            #p.save()
                            # DOSN'T WORK AS ps_product_lang uses composite pk!

                            logger.info("update ps17_product_lang set description=%s where id_product=%s and id_lang=%s and is_shop=%s")
                            logger.info(f"pars:{new_description},{p.id_product},{p.id_lang},{p.id_shop}")


                            with connections[db].cursor() as cursor:
                                cursor.execute("update ps17_product_lang set description=%s where id_product=%s and id_lang=%s and id_shop=%s",
                                    [new_description,p.id_product,p.id_lang,p.id_shop])

                            n_updated += 1
                            logger.info(f'saved:{p.id_product},{p.id_lang},{p.id_shop}')

            #end if obj['search']:

            # TODO: shop_context
            if obj['what']=='price':
                queryset = Ps17Product.objects.using(db).filter(id_product__in=ids,)
                l = len(queryset)
                logger.info(f'found:{l}')
                for p in queryset:
                    n += 1
                    new_price = obj['replace'].strip()
                    mult = False
                    if '*' in new_price:
                        if new_price[0]=='*' and new_price[1] in ['0','1','2','3','4','5','6','7','8','9']:
                            mult = True
                            new_price = new_price[1:]
                        else:
                            mult_arr = new_price.split()
                            if mult_arr[0] == '*':
                                mult = True
                                new_price = mult_arr[1]

                    logger.info(f"{n} {p.id_product}: {p.price}=>{new_price}:{id_shop}")

                    if id_shop:
                        if mult:
                            logger.info("update ps17_product_shop set price=price*%s where id_product=%s and id_shop=%s")
                        else:
                            logger.info("update ps17_product_shop set price=%s where id_product=%s and id_shop=%s")
                        logger.info(f"pars:{new_price},{p.id_product},{id_shop}")

                        with connections[db].cursor() as cursor:
                            if mult:
                                cursor.execute("update ps17_product_shop set price=price*%s where id_product=%s and id_shop=%s",[new_price,p.id_product,id_shop])
                            else:
                                cursor.execute("update ps17_product_shop set price=%s where id_product=%s and id_shop=%s",[new_price,p.id_product,id_shop])
                    else:
                        if mult:
                            logger.info("update ps17_product_shop set price=price*%s where id_product=%s")
                        else:
                            logger.info("update ps17_product_shop set price=%s where id_product=%s")
                        logger.info(f"pars:{new_price},{p.id_product}")

                        with connections[db].cursor() as cursor:
                            if mult:
                                cursor.execute("update ps17_product_shop set price=price*%s where id_product=%s",[new_price,p.id_product])
                                cursor.execute("update ps17_product set price=price*%s where id_product=%s",[new_price,p.id_product])
                            else:
                                cursor.execute("update ps17_product_shop set price=%s where id_product=%s",[new_price,p.id_product])
                                cursor.execute("update ps17_product set price=%s where id_product=%s",[new_price,p.id_product])

                    n_updated += 1
                    logger.info(f'saved:{p.id_product}')

            if obj['what']=='cost-price':
                queryset = Ps17Product.objects.using(db).filter(id_product__in=ids,)
                l = len(queryset)
                logger.info(f'found:{l}')
                for p in queryset:
                    n += 1
                    new_price = obj['replace'].strip()
                    mult = False
                    if '*' in new_price:
                        if new_price[0]=='*' and new_price[1] in ['0','1','2','3','4','5','6','7','8','9']:
                            mult = True
                            new_price = new_price[1:]
                        else:
                            mult_arr = new_price.split()
                            if mult_arr[0] == '*':
                                mult = True
                                new_price = mult_arr[1]

                    logger.info(f"{n} {p.id_product}: {p.wholesale_price}=>{new_price}:{id_shop}")

                    if id_shop:
                        if mult:
                            logger.info("update ps17_product_shop set wholesale_price=wholesale_price*%s where id_product=%s and id_shop=%s")
                        else:
                            logger.info("update ps17_product_shop set wholesale_price=%s where id_product=%s and id_shop=%s")
                        logger.info(f"pars:{new_price},{p.id_product},{id_shop}")

                        with connections[db].cursor() as cursor:
                            if mult:
                                cursor.execute("update ps17_product_shop set wholesale_price=wholesale_price*%s where id_product=%s and id_shop=%s",[new_price,p.id_product,id_shop])
                            else:
                                cursor.execute("update ps17_product_shop set wholesale_price=%s where id_product=%s and id_shop=%s",[new_price,p.id_product,id_shop])
                    else:
                        if mult:
                            logger.info("update ps17_product_shop set wholesale_price=wholesale_price*%s where id_product=%s")
                        else:
                            logger.info("update ps17_product_shop set wholesale_price=%s where id_product=%s")
                        logger.info(f"pars:{new_price},{p.id_product}")

                        with connections[db].cursor() as cursor:
                            if mult:
                                cursor.execute("update ps17_product_shop set wholesale_price=wholesale_price*%s where id_product=%s",[new_price,p.id_product])
                                cursor.execute("update ps17_product set wholesale_price=wholesale_price*%s where id_product=%s",[new_price,p.id_product])
                            else:
                                cursor.execute("update ps17_product_shop set wholesale_price=%s where id_product=%s",[new_price,p.id_product])
                                cursor.execute("update ps17_product set wholesale_price=%s where id_product=%s",[new_price,p.id_product])


                    n_updated += 1
                    logger.info(f'saved:{p.id_product}')

            if obj['what']=='weight':
                queryset = Ps17Product.objects.using(db).filter(id_product__in=ids,)
                l = len(queryset)
                logger.info(f'found:{l}')
                for p in queryset:
                    n += 1
                    new_weight = obj['replace']
                    logger.info(f"{n} {p.id_product}: {p.weight}=>{new_weight}")
                    if p.weight!=new_weight:

                        logger.info("update ps17_product set weight=%s where id_product=%s and id_shop=%s")
                        logger.info(f"pars:{new_weight},{p.id_product},1")


                        with connections[db].cursor() as cursor:
                            cursor.execute("update ps17_product set weight=%s where id_product=%s",[new_weight,p.id_product])

                        n_updated += 1
                        logger.info(f'saved:{p.id_product}')

        logger.error(f'done:{n}/{n_updated}')

        return Response({'success':1,'req':obj, 'count':n, 'updated':n_updated})                

    
