import numpy as np
import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime
from icecream import ic

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

        p = DailySalesData.get_data(par,get_site(request)) 

        if par=='y':
            html=p.to_html(columns=['Year','orders','products','GBP_cost','GBP_p_exVAT','VAT 20pc','GBP_products','GBP_shipping','GBP_paid','P estimated','Gross Margin','GM estimated'],index=False)

        elif par=='q':
            html=p.to_html(columns=['Quarter','orders','products','GBP_cost','GBP_p_exVAT','VAT 20pc','GBP_products','GBP_shipping','GBP_paid','P estimated','Gross Margin','GM estimated'],index=False)

        elif par=='m':
            html=p.to_html(columns=['Month','orders','products','GBP_cost','GBP_p_exVAT','VAT 20pc','GBP_products','GBP_shipping','GBP_paid','P estimated','Gross Margin','GM estimated'],index=False)

        elif par=='d':
            html=p.to_html(columns=['Date','orders','products','GBP_cost','GBP_p_exVAT','VAT 20pc','GBP_products','GBP_shipping','GBP_paid','Gross Margin'],index=False)

        elif par=='dw':
            html=p.to_html(columns=['DOW','orders','products','GBP_p_exVAT','VAT 20pc','GBP_products','Gross Margin'],index=False)

        elif par=='dm':
            html=p.to_html(columns=['Day','orders','products','GBP_p_exVAT','VAT 20pc','GBP_products','Gross Margin'],index=False)

        elif par=='mm':
            html=p.to_html(columns=['Month','orders','products','GBP_p_exVAT','VAT 20pc','GBP_products','Gross Margin'],index=False)

        elif par=='mavg':
            html=p.to_html(columns=['Year','orders','products','GBP_p_exVAT','VAT 20pc','GBP_products','Gross Margin'],index=False)

        elif par=='davg':
            html=p.to_html(columns=['Year','orders','products','GBP_p_exVAT','VAT 20pc','GBP_products','Gross Margin'],index=False)

        html=html.replace('class="dataframe"',
            'class="table is-bordered is-striped is-narrow is-hoverable is-fullwidth"'
        )
        html=html.replace('<td>NaN</td>','<td> </td>')

        return HttpResponse( html)

class SalesFigView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)     

    def get(self, request, *args, **kwargs):
        par = self.kwargs.get('par')

        p = DailySalesData.get_data(par,get_site(request)) 

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
            fig = px.line(p,x='Date',y=['GBP_products','Gross Margin',],
                labels={
                    'value':'GBP',
                    'variable':' ',
                },
                title="Daily sales (30 days)",width=1200, height=500)
            fig.update_xaxes(rangeslider_visible=True, dtick='M1')

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
        p = MonthlyCustomersData.get_data(par,get_site(request)) 

        if par=='y':
            p = p.rename(columns={'month':'year'})

        html=p.to_html(
                index=False,
                columns=['month' if par=='m' else 'year','customers','new_customers','%nc',
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
        p = MonthlyTotalCustomersData.get_data(par,get_site(request)) 

        html=p.to_html(
                index=False,
                columns=['year_mon','total_customers','live_customers','new_customers','lost_customers',],
                float_format='%d',
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
        p = CustomersBehaviourData.get_data(par,get_site(request)) 


        if par=='g':
            p = p.rename(columns={'id_customer':'customers'})
            html=p.to_html(
                columns=['group','customers','orders','avg_orders','order_first','order_last','total_gbp','avg_order_gbp','orders_apart_days'],
                index=False,
                na_rep=' ',
                #float_format='{:.2f}'.format,
                float_format='%d',
                classes="table is-bordered is-striped is-narrow is-hoverable is-fullwidth",
                table_id="table_by_group"
            )

        else:
            p.loc['--average--'] = None
            p.loc['--average--','total_gbp'] = 1000000
            
            p.sort_values('total_gbp',ascending=False,inplace=True)

            p.loc['--average--','total_gbp'] = None
            p.loc['--average--'] = p.mean().round()
            p.loc['--average--','order_due'] = None
            p.loc['--average--','order_missed'] = None
            p.loc['--average--','last_cart'] = None

            p.loc['--average--','order_first'] = p['order_first'].min()
            p.loc['--average--','order_last'] = p['order_last'].max()
            p.loc['--average--','customer_name'] = '--average customer--'

            html=p.to_html(
                columns=['customer_name','group','orders','order_first','order_last','total_gbp','avg_order_gbp','orders_apart_days','order_due','order_missed','last_cart'],
                index=False,
                na_rep=' ',
                #float_format='{:.2f}'.format,
                float_format='%d',
                classes="table is-bordered is-striped is-narrow is-hoverable is-fullwidth",
                table_id="table_by_customer"
            )

            css = """
<style>
#table_by_customer td:nth-child(10),
#table_by_customer th:nth-child(10) {
    display:none;
}
</style>
"""
            js = """
<script>
function isDateOlderThanMonths(dateString,m) {
  var currentDate = new Date();
  currentDate.setMonth(currentDate.getMonth() - m);
  
  var givenDate = new Date(dateString);
  
  return givenDate < currentDate;
}

$('#table_by_customer tr').each(function(){
    if (isDateOlderThanMonths($(this).find('td:nth-child(5)').text(),12)) {
        $(this).css('color','grey');

        if (parseFloat($(this).find('td:nth-child(6)').text()) < 100) {
            $(this).css('display','none');
        
        }
    }

    const d = parseInt(
            $(this).find('td:nth-child(10)').text()
        );
    if (isNaN(d)) {
        $(this).find('td:nth-child(9)').text(' ');
    }
    else if(
        d > 0
    ) {
        $(this).find('td:nth-child(1)').css('color','red');
        $(this).find('td:nth-child(5)').css('color','red');
        $(this).find('td:nth-child(9)').css('color','red');
    }
    else {
        $(this).find('td:nth-child(1)').css('color','green');
        $(this).find('td:nth-child(9)').css('color','green');
    
    }
});
</script>
"""
            html =  js + css + html

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
        
        p = ProductsData.get_data(par,get_site(request)) 

        if cat=='x':
            p = p[(p['bt']==0) & (p['gelclr']==0) & (p['procare']==0) & (p['soakoff']==0) & (p['fileoff']==0) & (p['acry']==0) & (p['qt']==0) & (p['outlet']==0) & (p['archive']==0)]
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


class StockTableView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)     

    def get(self, request, *args, **kwargs):
        par = self.kwargs.get('par')

        pars = par.split(':')
        par=pars[0]
        cat = None
        if len(pars) > 1: cat = pars[1]
        ic('par',par,cat)
        
        p = StockData.get_data(par,get_site(request)) 

        if par=='*':
            last_dt=max(p['date_add'])
            p=p[(p['date_add']==last_dt)]
            #p=p[(p['date_add']==last_dt) & (p['qnt']>0)]
            #p=p[p['qnt']<50]
           
            if cat=='x':
                p = p[(p['bt']==0) & (p['gelclr']==0) & (p['procare']==0) & (p['soakoff']==0) & (p['fileoff']==0) & (p['acry']==0) & (p['qt']==0) & (p['outlet']==0) & (p['archive']==0)]
            elif cat:
                p = p[p[cat]>0]
            p.sort_values(['qnt','reference'],ascending=True,inplace=True)

            #print (p['id_product'])
            p['out_of_stock'] = ' '

            #ic(len(p))

            if cat:
                for id in p['id_product']:
                    try:
                        p1 =StockData.get_data(id,get_site(request))  
                        #ic (id,p1.iloc[-1])
                        if p1.iloc[-1].get('getting_out'):
                            p.loc[p['id_product']==id,'out_of_stock'] = p1.iloc[-1]['date_add'].date()
                        else:
                            p.loc[p['id_product']==id,'out_of_stock'] = p1.iloc[-1]['date_out'].date() if p1.iloc[-1].get('date_out') else ''

                    except Exception as e:
                        ic ('except',e)                    

            

            html=p.to_html(
                    index=False,
                    columns=['id_product','reference','qnt','out_of_stock',],
                    na_rep=' ',
                    classes="table is-bordered is-striped is-narrow is-hoverable is-fullwidth",)
        else:
            #p.loc[p.index==max(p.index),'qnt']=p.iloc[-1]['reference']      
            #p.loc[p.index==max(p.index),'reference']=p.iloc[0]['reference']      

            #ic(p)
            p['move'] = p['qnt'].diff()   #.fillna(0).astype(int)

            html=p[::-1].to_html(
                    index=False,
                    columns=['reference','qnt','move','date_add'],
                    na_rep=' ',
                    float_format='%d',
                    classes="table is-bordered is-striped is-narrow is-hoverable is-fullwidth",
            )

        return HttpResponse(html)

class StockFigView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)     

    def get(self, request, *args, **kwargs):
        par = self.kwargs.get('par')

        print('StockFigView:'+par)

        p = StockData.get_data(par,get_site(request)) 
        #print(p[0:5])

        if par!='*':
            
            fig = px.line(p,x=p['date_add'], y=['qnt','predicton'],
                title="Stock level: "+p.iloc[0]['reference'],
                labels={
                    'value':'Stock level',
                    'variable':'Stock level',
                },width=1200, height=500)
            fig.update_xaxes(rangeslider_visible=False, dtick='M1')

            return JsonResponse(fig,safe=False,encoder=plotly.utils.PlotlyJSONEncoder)

        return HttpResponse('no id_product')
