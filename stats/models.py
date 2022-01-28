import numpy as np
import pandas as pd
import os
import time

from django.db import models
from django.conf import settings

def raw_queryset_as_values_list(raw_qs):
    columns = raw_qs.columns
    for row in raw_qs:
        #yield tuple({col:getattr(row, col)} for col in columns)
        yield tuple(getattr(row, col) for col in columns)

class DailySalesData(models.Model):
    date_add = models.DateField(primary_key=True)
    products = models.IntegerField(blank=True,null=True)
    orders = models.IntegerField(blank=True,null=True)
    GBP_cost = models.FloatField(blank=True,null=True)
    GBP_products = models.FloatField(blank=True,null=True)
    GBP_shipping = models.FloatField(blank=True,null=True)
    GBP_paid = models.FloatField(blank=True,null=True)

    @staticmethod
    def dtypes():
        return {
            'date_add':'M',
            'products':'i',
            'orders':'i',
            'GBP_cost':'float64',
            'GBP_products':'float64',
            'GBP_shipping':'float64',
            'GBP_paid':'float64',
        }

    @staticmethod
    def SQL():

        #SUM((SELECT SUM(product_quantity) FROM ps17_order_detail d WHERE id_order=o.id_order AND reduction_percent>0)) products_discounted,

        sql = f"""
SELECT
date(date_add) date_add,
SUM((SELECT SUM(product_quantity) FROM ps17_order_detail d WHERE id_order=o.id_order)) products,
COUNT(id_order) orders,
ROUND((
SUM((SELECT SUM(original_wholesale_price) FROM ps17_order_detail d WHERE id_order=o.id_order)) 
    ),2) GBP_cost
,
ROUND(SUM((total_products_wt-total_discounts_tax_incl)/conversion_rate) ,2) GBP_products,
ROUND(SUM((total_shipping_tax_incl)/conversion_rate) ,2) GBP_shipping,
ROUND(SUM((total_paid_real)/conversion_rate) ,2) GBP_paid
FROM `ps17_orders` o
WHERE current_state IN
(SELECT id_order_state FROM ps17_order_state WHERE paid=1)
and date_add>='2019-01-01'
GROUP BY date(date_add)
ORDER BY date_add DESC
        """

        return sql        

    def get_data(par='d'):
        store_path = settings.MEDIA_ROOT + '/statsdata-v2.pkl'
        
        try:
            tm = os.path.getmtime(store_path) 
            if int(time.time())-int(tm) > 24 * 60 * 60:
                raise Exception("Cache expired")

            p = pd.read_pickle(store_path)
        except Exception as e:
            print (e)
            queryset = DailySalesData.objects.using('presta').raw(DailySalesData.SQL())
            p = pd.DataFrame(raw_queryset_as_values_list(queryset), columns=list(queryset.columns))
            p = p.astype(DailySalesData.dtypes())

            p['Y'] = p['date_add'].dt.year
            p['M'] = p['date_add'].dt.month
            p['D'] = p['date_add'].dt.day
            p['Q'] = p['date_add'].dt.quarter
            p['DOY'] = p['date_add'].dt.day_of_year
            p['DOW'] = p['date_add'].dt.day_of_week
            p['DIM'] = p['date_add'].dt.days_in_month

            p['VAT 8pc'] = round(p['GBP_products']*0.08,2)
            p['Gross Margin'] = round(p['GBP_products'] - p['VAT 8pc'] - p['GBP_cost'],2)

            p.to_pickle(store_path)

        if par=='y':
            p = p.groupby(['Y',]).agg({'products':np.sum,
                                                'orders':np.sum,
                                                'GBP_cost':np.sum,
                                                'GBP_products':np.sum,
                                                'GBP_shipping':np.sum,
                                                'GBP_paid':np.sum,
                                                'VAT 8pc':np.sum,
                                                'Gross Margin':np.sum,
                                                'DOY':np.max
                                                }).sort_index(ascending=False)
            p['Year'] = p.index
            p.loc[p.index[0],'P estimated'] = round(p.loc[p.index[0],'GBP_products']*365/p.loc[p.index[0],'DOY'],2)
            p.loc[p.index[0],'GM estimated'] = round(p.loc[p.index[0],'Gross Margin']*365/p.loc[p.index[0],'DOY'],2)

        elif par=='q':
            p = p.groupby(['Y','Q']).agg({'products':np.sum,
                                                'orders':np.sum,
                                                'GBP_cost':np.sum,
                                                'GBP_products':np.sum,
                                                'GBP_shipping':np.sum,
                                                'GBP_paid':np.sum,
                                                'VAT 8pc':np.sum,
                                                'Gross Margin':np.sum,
                                                'D':np.max,
                                                'M':np.max
                                                }).sort_index(ascending=False)
            p.reset_index(inplace=True)
            p['Y-M'] = p['Y'].astype(str)+'-'+(1+3*(p['Q'].astype(int)-1)).astype(str)
            p['Quarter'] = p['Y'].astype(str)+'-'+p['Q'].astype(str)

            m = p.loc[p.index[0],'M']%3-1
            p.loc[p.index[0],'P estimated'] = round(p.loc[p.index[0],'GBP_products']*90 / (p.loc[p.index[0],'D']+(m)*30),2)
            p.loc[p.index[0],'GM estimated'] = round(p.loc[p.index[0],'Gross Margin']*90 / (p.loc[p.index[0],'D']+(m)*30),2)

        elif par=='m':
            p = p.groupby(['Y','Q','M']).agg({'products':np.sum,
                                                'orders':np.sum,
                                                'GBP_cost':np.sum,
                                                'GBP_products':np.sum,
                                                'GBP_shipping':np.sum,
                                                'GBP_paid':np.sum,
                                                'VAT 8pc':np.sum,
                                                'Gross Margin':np.sum,
                                                'D':np.max
                                                }).sort_index(ascending=False)
            p.reset_index(inplace=True)
            p['Month'] = p['Y'].astype(str)+'-'+p['M'].astype(str)
            p.loc[p.index[0],'P estimated'] = round(p.loc[p.index[0],'GBP_products']*30/p.loc[p.index[0],'D'],2)
            p.loc[p.index[0],'GM estimated'] = round(p.loc[p.index[0],'Gross Margin']*30/p.loc[p.index[0],'D'],2)

        elif par=='d':
            p['Date'] = p['date_add'].astype(str)
            p.sort_index(ascending=False,inplace=True)
            p.reset_index(inplace=True)

            p['P 7day avg'] = p['GBP_products'].rolling(7).mean()
            p['GM 7day avg'] = p['Gross Margin'].rolling(7).mean()

            p.sort_index(ascending=False,inplace=True)
            p.reset_index(inplace=True)
            p = p[0:30]

        elif par=='dw':
            p = p.groupby(['DOW']).agg({'products':np.sum,
                                                'GBP_cost':np.mean,
                                                'GBP_products':np.mean,
                                                'GBP_shipping':np.mean,
                                                'GBP_paid':np.mean,
                                                'VAT 8pc':np.mean,
                                                'Gross Margin':np.mean,
                                                }).sort_index(ascending=False)
            p.reset_index(inplace=True)

            p['DOW'] = p.index+1
            p['GBP_products'] = round(p['GBP_products'],2)
            p['GBP_products_e'] = p['GBP_products'] - p['Gross Margin']

        elif par=='dm':
            p = p.groupby(['D']).agg({'products':np.sum,
                                                'GBP_cost':np.mean,
                                                'GBP_products':np.mean,
                                                'GBP_shipping':np.mean,
                                                'GBP_paid':np.mean,
                                                'VAT 8pc':np.mean,
                                                'Gross Margin':np.mean,
                                                }).sort_index(ascending=False)
            p.reset_index(inplace=True)

            p['Day'] = p.index+1
            p['GBP_products'] = round(p['GBP_products'],2)
            p['GBP_products_e'] = p['GBP_products'] - p['Gross Margin']

        elif par=='mm':
            p = p.groupby(['M']).agg({'products':np.sum,
                                                'GBP_cost':np.mean,
                                                'GBP_products':np.mean,
                                                'GBP_shipping':np.mean,
                                                'GBP_paid':np.mean,
                                                'VAT 8pc':np.mean,
                                                'Gross Margin':np.mean,
                                                }).sort_index(ascending=False)
            p.reset_index(inplace=True)

            p['Month'] = p.index+1
            p['GBP_products'] = round(p['GBP_products'],2)
            p['GBP_products_e'] = p['GBP_products'] - p['Gross Margin']

        elif par=='mavg':
            p1 = p.groupby(['Y','M']).agg({'products':np.sum,
                                                'orders':np.sum,
                                                'GBP_products':np.sum,
                                                'Gross Margin':np.sum,
                                                }).sort_index(ascending=False)
            p2 = p1.groupby(['Y',]).agg({'products':np.mean,
                                                'orders':np.mean,
                                                'GBP_products':np.mean,
                                                'Gross Margin':np.mean,

                                                }).sort_index(ascending=False)
            p2['products'] = round(p2['products'],2)
            p2['orders'] = round(p2['orders'],2)
            p2['GBP_products'] = round(p2['GBP_products'],2)
            p2['Gross Margin'] = round(p2['Gross Margin'],2)

            p2.loc['All Time'] = p2.mean()

            p2['Year'] = p2.index

            return p2                                                

        elif par=='davg':
            p1 = p.groupby(['Y','M']).agg({'products':np.mean,
                                                'orders':np.mean,
                                                'GBP_products':np.mean,
                                                'Gross Margin':np.mean,
                                                }).sort_index(ascending=False)
            p2 = p1.groupby(['Y',]).agg({'products':np.mean,
                                                'orders':np.mean,
                                                'GBP_products':np.mean,
                                                'Gross Margin':np.mean,

                                                }).sort_index(ascending=False)
            p2['products'] = round(p2['products'],2)
            p2['orders'] = round(p2['orders'],2)
            p2['GBP_products'] = round(p2['GBP_products'],2)
            p2['Gross Margin'] = round(p2['Gross Margin'],2)
            
            p2.loc['All Time'] = p2.mean()
            p2['Year'] = p2.index

            return p2                                                

        return p

# ---
class DailySales(models.Model):
    day = models.CharField(primary_key=True,max_length=20)
    products = models.IntegerField(blank=True,null=True)
    products_discounted = models.IntegerField(blank=True,null=True)
    orders = models.IntegerField(blank=True,null=True)
    GBP_products = models.FloatField(blank=True,null=True)
    GBP_8vat = models.FloatField(blank=True,null=True)
    GBP_products_8vat = models.FloatField(blank=True,null=True)
    gross_margin = models.FloatField(blank=True,null=True)
    gross_margin_percent = models.FloatField(blank=True,null=True)

    @staticmethod
    def SQL(par='d'):
        digits = 4 if par=='y' else 7 if par=='m' else 10

        sql = f"""
SELECT
substr(date_add,1,{digits}) day,
sum((select sum(product_quantity) from ps17_order_detail d where id_order=o.id_order)) products,
sum((select sum(product_quantity) from ps17_order_detail d where id_order=o.id_order and reduction_percent>0)) products_discounted,
count(id_order) orders,
round(sum((total_products_wt-total_discounts_tax_incl)/conversion_rate) ,2) GBP_products,
round(0.08*sum((total_products_wt-total_discounts_tax_incl)/conversion_rate) ,2) GBP_8vat,
round(0.92*sum((total_products_wt-total_discounts_tax_incl)/conversion_rate) ,2) GBP_products_8vat,
round((
0.92*sum((total_products_wt-total_discounts_tax_incl)/conversion_rate)  -
sum((select sum(original_wholesale_price) from ps17_order_detail d where id_order=o.id_order)) 
    ),2) gross_margin
,
round((
(0.92*sum((total_products_wt-total_discounts_tax_incl)/conversion_rate)  -
sum((select sum(original_wholesale_price) from ps17_order_detail d where id_order=o.id_order)) 
) * 100 /
(0.92*sum((total_products_wt-total_discounts_tax_incl)/conversion_rate))
),2) gross_margin_percent

FROM `ps17_orders` o
where current_state in
(2,3,4,5,17,20,21,31,35,39,40)

group by
substr(date_add,1,{digits})
order by 1 
        """

        return sql

