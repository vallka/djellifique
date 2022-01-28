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

        return JsonResponse(fig,safe=False,encoder=plotly.utils.PlotlyJSONEncoder)


# ---

def raw_queryset_as_values_list(raw_qs):
    columns = raw_qs.columns
    for row in raw_qs:
        #yield tuple({col:getattr(row, col)} for col in columns)
        yield tuple(getattr(row, col) for col in columns)

class YearlySalesView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)     

    def get(self, request, *args, **kwargs):
        queryset = DailySales.objects.using('presta').raw(DailySales.SQL('y'))

        p = pd.DataFrame(raw_queryset_as_values_list(queryset), columns=list(queryset.columns))

        fig = px.line(p,x='day', y='GBP_products',title="Yearly sales",width=1200, height=500)
        fig.update_xaxes(rangeslider_visible=True, 
            dtick="Y1",
        )

        return JsonResponse(fig,safe=False,encoder=plotly.utils.PlotlyJSONEncoder)

class MonthlySalesView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)     

    def get(self, request, *args, **kwargs):
        queryset = DailySales.objects.using('presta').raw(DailySales.SQL('m'))
        p = pd.DataFrame(raw_queryset_as_values_list(queryset), columns=list(queryset.columns))

        fig = px.line(p,x='day', y='GBP_products',title="Monthly sales", width=1200, height=500)

        fig.update_xaxes(rangeslider_visible=True, 
            dtick="M1",
            tickformat="%b\n%Y",
        )

        return JsonResponse(fig,safe=False,encoder=plotly.utils.PlotlyJSONEncoder)


class DailySalesView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)     

    def get(self, request, *args, **kwargs):
        queryset = DailySales.objects.using('presta').raw(DailySales.SQL('d'))
        p = pd.DataFrame(raw_queryset_as_values_list(queryset), columns=list(queryset.columns))

        fig = px.line(p,x='day', y='GBP_products',title="Daily sales", width=1200, height=500)
        fig.update_xaxes(rangeslider_visible=True, 
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
               ])
            )
        )

        return JsonResponse(fig,safe=False,encoder=plotly.utils.PlotlyJSONEncoder)
