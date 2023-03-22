import os
import json
import pprint
import requests
import base64
from PIL import Image

from rest_framework import viewsets,generics
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated 
from rest_framework.response import Response
from rest_framework.exceptions import ParseError
from rest_framework.parsers import JSONParser
from drf_yasg.utils import swagger_auto_schema
from django.conf import settings
from django.db import connections

from .models import *
from .views import *

class UPSListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)     
    serializer_class = UPSSerializer

    def get(self, request, *args, **kwargs):
        ids = kwargs.get('ids', '')

        queryset = UPSParcel.objects.using('presta').raw(UPSParcel.UPS_sql(kwargs.get('ids', '')))

        #logger.info(f'UPSListView:{ids}')
        #logger.error(queryset)

        serializer = self.get_serializer(queryset, many=True)
    
        return Response(serializer.data)                


class UPSAction(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)     
    parser_class = (JSONParser,)
    serializer_class = UPSSerializer

    @swagger_auto_schema(operation_description="UPS description")
    def post(self, request, format=None):

        obj = request.data

        print(obj)

        queryset = UPSParcel.objects.using('presta').raw(UPSParcel.UPS_sql(obj['id_order']))
        if len(queryset)==0:
            return Response({'status':'Error','message':f"Order id={obj['id_order']} not found"})


        serializer = self.get_serializer(queryset, many=True)

        resp = processItem(serializer.data[0],obj['id_order'])
        if resp.get('response') and resp.get('response').get('errors'):
            return Response({'status': 'Error','data':resp,'message':resp['response']['errors'][0]['message']})

        #logger.error('####' + resp["ShipmentResponse"]["ShipmentResults"]["ShipmentIdentificationNumber"])

        shipping_no = resp["ShipmentResponse"]["ShipmentResults"]["ShipmentIdentificationNumber"]

        with connections['presta'].cursor() as cursor:
            cursor.execute("UPDATE ps17_orders SET shipping_number=%s,current_state=31 WHERE id_order=%s", [shipping_no,obj['id_order']])
            cursor.execute("update ps17_order_carrier set tracking_number=%s where id_order=%s", [shipping_no,obj['id_order']])
            
            cursor.execute("insert into ps17_order_history (id_employee,id_order,id_order_state,date_add) values (%s,%s,%s,now())", [0,obj['id_order'],31])

        return Response({'status': 'OK','data':resp})

def processItem(dat,id_order):
    newHeaders = {
        'Content-type': 'application/json', 
        'Accept': 'application/json',
        'Username': os.environ.get('UPS_USERNAME'),
        'Password': os.environ.get('UPS_PASSWORD'),
        'AccessLicenseNumber': os.environ.get('UPS_ACCESSLICENSENUMBER'),
        'transId': 'Transaction001',
        'transactionSrc': 'test'
    }

    rn = dat['ShipmentRequest']['Shipment']['ReferenceNumber']['Value']
    path = settings.MEDIA_ROOT + '/UPS/'

    response = requests.post(' https://onlinetools.ups.com/ship/v1807/shipments',data=json.dumps(dat),headers=newHeaders)
    #response = requests.post(' https://wwwcie.ups.com/ship/v1807/shipments',data=json.dumps(dat),headers=newHeaders)

    #print("Status code: ", response.status_code)
    jsn = json.loads(response.text)

    if response.status_code==200:
        with open(f"{path}{id_order}.json", "w") as file:
            file.write(response.text)


        with open(f"{path}{id_order}.gif", "wb") as file:
            file.write(base64.b64decode(jsn["ShipmentResponse"]["ShipmentResults"]["PackageResults"]["ShippingLabel"]["GraphicImage"]))    

        pdf = Image.open(f"{path}{id_order}.gif")    
        pdf.save(f"{path}{id_order}.pdf", "PDF" ,resolution=100.0, save_all=True)

        return jsn
    else:
        return jsn

class UPSLabelAction(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)     
    parser_class = (JSONParser,)
    serializer_class = UPSLabelSerializer

    @swagger_auto_schema(operation_description="UPS description - label")
    def post(self, request, format=None):

        obj = request.data
        queryset = ShippingNumber.objects.using('presta').raw(ShippingNumber.ShippingNumber_sql(obj['id_order']))

        if len(queryset)==0:
            return Response({'status':'Error','message':f"Order id={obj['id_order']} not found"})

        if not queryset[0].ShippingNumber:
            return Response({'status':'Error','message':f"Order id={obj['id_order']} has no tracking number"})

        #logger.error(queryset)

        serializer = self.get_serializer(queryset, many=True)

        resp = processLabelItem(serializer.data[0],obj['id_order'])

        if resp.get('response') and resp.get('response').get('errors'):
            return Response({'status': 'Error','data':resp,'message':resp['response']['errors'][0]['message']})

        #logger.error('####' + resp["LabelRecoveryResponse"]["ShipmentIdentificationNumber"])

        return Response({'status': 'OK','data':resp,})

def processLabelItem(dat,id_order):
    newHeaders = {
        'Content-type': 'application/json', 
        'Accept': 'application/json',
        'Username': os.environ.get('UPS_USERNAME'),
        'Password': os.environ.get('UPS_PASSWORD'),
        'AccessLicenseNumber': os.environ.get('UPS_ACCESSLICENSENUMBER'),
        'transId': 'Transaction001',
        'transactionSrc': 'test'
    }

    path = settings.MEDIA_ROOT + '/UPS/'

    response = requests.post(' https://onlinetools.ups.com/ship/v1/shipments/labels',data=json.dumps(dat),headers=newHeaders)

    #print("Status code: ", response.status_code)
    jsn = json.loads(response.text)

    if response.status_code==200:
        with open(f"{path}{id_order}.json", "w") as file:
            file.write(response.text)

        #logger.error(jsn)
        with open(f"{path}{id_order}.gif", "wb") as file:
            file.write(base64.b64decode(jsn["LabelRecoveryResponse"]["LabelResults"]["LabelImage"]["GraphicImage"]))    

        pdf = Image.open(f"{path}{id_order}.gif")    
        pdf.save(f"{path}{id_order}.pdf", "PDF" ,resolution=100.0, save_all=True)

        return jsn
    else:
        return jsn
