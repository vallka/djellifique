import numpy as np
import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objects as go
import json

from rest_framework import viewsets,generics
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated 
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from django.conf import settings
from django.db import connections
from django.core import serializers
from django.http import JsonResponse,HttpResponse

from .models import *
from .views import *


class SalesTableView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)     

    def get(self, request, *args, **kwargs):
        par = self.kwargs.get('par')

        p = DailySalesData.get_data(par) 

        if par=='y':
            html=p.to_html(columns=['Year','orders','products','GBP_paid','GBP_shipping','VAT 8pc','GBP_cost','GBP_products','P estimated','Gross Margin','GM estimated'],index=False)

        elif par=='q':
            html=p.to_html(columns=['Quarter','orders','products','GBP_paid','GBP_shipping','VAT 8pc','GBP_cost','GBP_products','P estimated','Gross Margin','GM estimated'],index=False)

        elif par=='m':
            html=p.to_html(columns=['Month','orders','products','GBP_paid','GBP_shipping','VAT 8pc','GBP_cost','GBP_products','P estimated','Gross Margin','GM estimated'],index=False)

        elif par=='d':
            html=p.to_html(columns=['Date','orders','products','GBP_paid','GBP_shipping','VAT 8pc','GBP_cost','GBP_products','Gross Margin'],index=False)

        elif par=='dw':
            html=p.to_html(columns=['DOW','GBP_products','Gross Margin'],index=False)

        elif par=='dm':
            html=p.to_html(columns=['Day','GBP_products','Gross Margin'],index=False)

        elif par=='mm':
            html=p.to_html(columns=['Month','GBP_products','Gross Margin'],index=False)

        elif par=='mavg':
            html=p.to_html(columns=['Year','orders','products','GBP_products','Gross Margin'],index=False)

        elif par=='davg':
            html=p.to_html(columns=['Year','orders','products','GBP_products','Gross Margin'],index=False)

        html=html.replace('class="dataframe"',
            'class="table is-bordered is-striped is-narrow is-hoverable is-fullwidth"'
        )
        html=html.replace('<td>NaN</td>','<td> </td>')

        return HttpResponse( html)

class SalesFigView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)     

    def get(self, request, *args, **kwargs):
        par = self.kwargs.get('par')

        p = DailySalesData.get_data(par) 

        if par=='y':
            p.loc[p.index[1],'P estimated'] = p.loc[p.index[1],'GBP_products']
            p.loc[p.index[1],'GM estimated'] = p.loc[p.index[1],'Gross Margin']

            fig = px.line(p,x=p.index, y=['GBP_products','P estimated','Gross Margin','GM estimated'],
                labels={
                    'value':'GBP',
                    'variable':' ',
                    'Y':'Year'
                },
                title="Yearly sales",
                width=1200, height=500)
            fig.update_xaxes(rangeslider_visible=False, dtick='Y1')

        elif par=='q':
            p.loc[p.index[1],'P estimated'] = p.loc[p.index[1],'GBP_products']
            p.loc[p.index[1],'GM estimated'] = p.loc[p.index[1],'Gross Margin']

            fig = px.line(p,x='Y-M', y=['GBP_products','P estimated','Gross Margin','GM estimated'],
                labels={
                    'value':'GBP',
                    'variable':' ',
                    'Y-M':'Quarter (month starts)'
                },
                title="Quarterly sales",width=1200, height=500)
            fig.update_xaxes(rangeslider_visible=True, dtick='M3')

        elif par=='m':
            p.loc[p.index[1],'P estimated'] = p.loc[p.index[1],'GBP_products']
            p.loc[p.index[1],'GM estimated'] = p.loc[p.index[1],'Gross Margin']

            fig = px.line(p,x='Month', y=['GBP_products','P estimated','Gross Margin','GM estimated'],
                labels={
                    'value':'GBP',
                    'variable':' ',
                },
                title="Monthly sales",width=1200, height=500)
            fig.update_xaxes(rangeslider_visible=True, dtick='M1')

        elif par=='d':
            fig = px.line(p,x='Date',y=['GBP_products','P 7day avg','Gross Margin','GM 7day avg'],
                labels={
                    'value':'GBP',
                    'variable':' ',
                },
                title="Daily sales (30 days)",width=1200, height=500)
            fig.update_xaxes(rangeslider_visible=True, dtick='D1')

        elif par=='dw':
            fig = px.bar(p,x='DOW',y=['Gross Margin','GBP_products_e',],
                labels={
                    'value':'GBP',
                    'DOW':'Day',
                    'variable':' ',
                    'GBP_products_e': 'GBP_products'
                },
                title="Daily average by Day of week",width=1200, height=500)
            fig.update_xaxes(rangeslider_visible=False, dtick='D1')

        elif par=='dm':
            fig = px.bar(p,x='Day',y=['Gross Margin','GBP_products_e',],
                labels={
                    'value':'GBP',
                    'variable':' ',
                    'GBP_products_e': 'GBP_products'
                },
                title="Daily average by Day of month",width=1200, height=500)
            fig.update_xaxes(rangeslider_visible=False, dtick='D1')

        elif par=='mm':
            fig = px.bar(p,x='Month',y=['Gross Margin','GBP_products_e',],
                labels={
                    'value':'GBP',
                    'variable':' ',
                    'GBP_products_e': 'GBP_products'
                },
                title="Daily average by Month of year",width=1200, height=500)
            fig.update_xaxes(rangeslider_visible=False, dtick='M1')

        elif par=='mavg':
            fig = px.line(p,x='Year',y=['GBP_products','Gross Margin',],
                labels={
                    'value':'GBP',
                    'variable':' ',
                },
                title="Monthly Averages",width=1200, height=500)
            fig.update_xaxes(rangeslider_visible=True, dtick='D1')

        elif par=='davg':
            fig = px.line(p,x='Year',y=['GBP_products','Gross Margin',],
                labels={
                    'value':'GBP',
                    'variable':' ',
                },
                title="Daily Averages",width=1200, height=500)
            fig.update_xaxes(rangeslider_visible=True, dtick='D1')

        return JsonResponse(fig,safe=False,encoder=plotly.utils.PlotlyJSONEncoder)

class CustomersTableView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)     

    def get(self, request, *args, **kwargs):
        par = self.kwargs.get('par')

        print('par',par)
        p = MonthlyCustomersData.get_data(par) 

        if par=='y':
            p = p.rename(columns={'month':'year'})

        html=p.to_html(
                index=False,
                columns=['month' if par=='m' else 'year','customers','new_customers','%nc','last_customers',
                    'orders','new_orders','%no',
                    'sales','new_sales','%ns',
                    'registrations','registrations_customers',],
        )

        html=html.replace('class="dataframe"',
            'class="table is-bordered is-striped is-narrow is-hoverable is-fullwidth"'
        )
        html=html.replace('<td>NaN</td>','<td> </td>')

        return HttpResponse(html)

class TotalCustomersTableView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)     

    def get(self, request, *args, **kwargs):
        par = self.kwargs.get('par')

        print('par',par)
        p = MonthlyTotalCustomersData.get_data(par) 

        html=p.to_html(
                index=False,
                columns=['month','total_customers','loyal_customers',],
        )

        html=html.replace('class="dataframe"',
            'class="table is-bordered is-striped is-narrow is-hoverable is-fullwidth"'
        )
        html=html.replace('<td>NaN</td>','<td> </td>')

        return HttpResponse(html)

class CustomersBehaviourTableView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)     

    def get(self, request, *args, **kwargs):
        par = self.kwargs.get('par')

        print('par=',par)
        p = CustomersBehaviourData.get_data(par) 


        if par=='g':
            p = p.rename(columns={'id_customer':'customers'})
            html=p.to_html(
                columns=['group','customers','orders','avg_orders','order_first','order_last','total_gbp','avg_order_gbp','orders_apart_days'],
                index=False,
                na_rep=' ',
                float_format='{:.2f}'.format,
            )

        else:
            p.loc['--average--'] = None
            p.loc['--average--','total_gbp'] = 1000000
            
            p.sort_values('total_gbp',ascending=False,inplace=True)

            p.loc['--average--','total_gbp'] = None
            p.loc['--average--'] = p.mean()

            p.loc['--average--','order_first'] = p['order_first'].min()
            p.loc['--average--','order_last'] = p['order_last'].max()
            p.loc['--average--','customer_name'] = '--average customer--'

            html=p.to_html(
                columns=['customer_name','group','orders','order_first','order_last','total_gbp','avg_order_gbp','orders_apart_days'],
                index=False,
                na_rep=' ',
                float_format='{:.2f}'.format,
            )

        html=html.replace('class="dataframe"',
            'class="table is-bordered is-striped is-narrow is-hoverable is-fullwidth"'
        )
        #html=html.replace('<td>NaN</td>','<td> </td>')

        return HttpResponse(html)

class ProductsTableView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)     

    def get(self, request, *args, **kwargs):
        par = self.kwargs.get('par')

        pars = par.split(':')
        par=pars[0]
        cat = None
        if len(pars) > 1: cat = pars[1]
        print('par',par,cat)
        
        p = ProductsData.get_data(par) 

        if cat=='x':
            p = p[(p['bt']==0) & (p['gelclr']==0) & (p['acry']==0) & (p['hb']==0) & (p['apex']==0) & (p['qt']==0)]
        elif cat:
            p = p[p[cat]>0]
        else:    
            p = p[p['months_in_sale']>1]

        if par in ['name','sold','per_month','months_in_sale','min_date','max_date']:
            p.sort_values(par,ascending=True,inplace=True)
        elif par in ['-name','-sold','-per_month','-months_in_sale','-min_date','-max_date']: 
            p.sort_values(par[1:],ascending=False,inplace=True)

        p.reset_index(inplace=True)
        p['place'] = p.index+1


        html=p.to_html(
                index=False,
                columns=['place','name','sold','per_month','months_in_sale','min_date','max_date'],
                na_rep=' ',
                float_format='{:.2f}'.format,
                classes="table is-bordered is-striped is-narrow is-hoverable is-fullwidth",
        )

        return HttpResponse(html)
