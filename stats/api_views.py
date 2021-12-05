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

class SalesTableView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)     

    def get(self, request, *args, **kwargs):
        par = self.kwargs.get('par')

        p = DailySales2.get_data(par) 

        html=p.to_html(columns=['Y-M','products','orders','GBP_cost','GBP_products','GBP_shipping','GBP_paid','VAT 8pc','Gross Margin'],index=False)
        html=html.replace('class="dataframe"',
            'class="table is-bordered is-striped is-narrow is-hoverable is-fullwidth"'
        )

        return HttpResponse( html)

class SalesFigView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)     

    def get(self, request, *args, **kwargs):
        par = self.kwargs.get('par')

        p = DailySales2.get_data(par) 
        if par=='q':
            fig = px.line(p,x='Y-M', y=['GBP_products','Gross Margin'],title="Quarterly sales",width=1200, height=500)
            fig.update_xaxes(rangeslider_visible=True, dtick='M3')
        elif par=='m':
            fig = px.line(p,x='Y-M', y=['GBP_products','Gross Margin'],title="Monthly sales",width=1200, height=500)
            fig.update_xaxes(rangeslider_visible=True, dtick='M1')
        elif par=='d':
            fig = px.line(p,x='date_add',y=['GBP_products','Gross Margin'],title="Daily sales",width=1200, height=500)
            fig.update_xaxes(rangeslider_visible=True, dtick='M1')
        else:    #y
            fig = px.line(p,x=p.index, y=['GBP_products','Gross Margin'],title="Yearly sales",width=1200, height=500)
            fig.update_xaxes(rangeslider_visible=True, dtick='Y1')

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
