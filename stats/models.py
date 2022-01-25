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
    y = models.IntegerField(blank=True,null=True)
    q = models.IntegerField(blank=True,null=True)
    m = models.IntegerField(blank=True,null=True)
    d = models.IntegerField(blank=True,null=True)
    products = models.IntegerField(blank=True,null=True)
    #products_discounted = models.IntegerField(blank=True,null=True)
    orders = models.IntegerField(blank=True,null=True)
    GBP_products = models.FloatField(blank=True,null=True)
    GBP_shipping = models.FloatField(blank=True,null=True)
    GBP_paid = models.FloatField(blank=True,null=True)

    @staticmethod
    def SQL():

        #SUM((SELECT SUM(product_quantity) FROM ps17_order_detail d WHERE id_order=o.id_order AND reduction_percent>0)) products_discounted,

        sql = f"""
SELECT
date(date_add) date_add,
YEAR(DATE_ADD) Y,
QUARTER(DATE_ADD) Q,
MONTH(DATE_ADD) M,
DAY(DATE_ADD) D,
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
GROUP BY Y,m,d
ORDER BY Y DESC,m DESC,d DESC
        """

        return sql        

    def get_data(par='d'):
        store_path = settings.MEDIA_ROOT + '/statsdata.pkl'
        
        try:
            tm = os.path.getmtime(store_path) 
            if int(time.time())-int(tm) > 24 * 60 * 60:
                raise Exception("Cache expired")

            p = pd.read_pickle(store_path)
        except Exception as e:
            print (e)
            queryset = DailySalesData.objects.using('presta').raw(DailySalesData.SQL())
            p = pd.DataFrame(raw_queryset_as_values_list(queryset), columns=list(queryset.columns))
            p.to_pickle(store_path)
            pass


        if par=='y':
            p['DOY'] = pd.to_datetime(p['date_add']).dt.day_of_year
        if par=='dw':
            p['DOW'] = pd.to_datetime(p['date_add']).dt.day_of_week


        if par=='y':
            p = p.groupby(['Y',]).agg({'products':np.sum,
                                                'orders':np.sum,
                                                'GBP_cost':np.sum,
                                                'GBP_products':np.sum,
                                                'GBP_shipping':np.sum,
                                                'GBP_paid':np.sum,
                                                'DOY':np.max
                                                }).sort_index(ascending=False)
            p['Y-M'] = p.index
            p['Year'] = p.index

        elif par=='q':
            p = p.groupby(['Y','Q']).agg({'products':np.sum,
                                                'orders':np.sum,
                                                'GBP_cost':np.sum,
                                                'GBP_products':np.sum,
                                                'GBP_shipping':np.sum,
                                                'GBP_paid':np.sum,
                                                'D':np.max,
                                                'M':np.max
                                                }).sort_index(ascending=False)
            p.reset_index(inplace=True)
            p['Y-M'] = p['Y'].astype(str)+'-'+(1+3*(p['Q'].astype(int)-1)).astype(str)
            p['Y-Q'] = p['Y'].astype(str)+'-'+p['Q'].astype(str)
        elif par=='m':
            p = p.groupby(['Y','Q','M']).agg({'products':np.sum,
                                                'orders':np.sum,
                                                'GBP_cost':np.sum,
                                                'GBP_products':np.sum,
                                                'GBP_shipping':np.sum,
                                                'GBP_paid':np.sum,
                                                'D':np.max
                                                }).sort_index(ascending=False)
            p.reset_index(inplace=True)
            p['Y-M'] = p['Y'].astype(str)+'-'+p['M'].astype(str)
        elif par=='d':
            p['Y-M'] = p['date_add'].astype(str)
            p.sort_index(ascending=False,inplace=True)
            p.reset_index(inplace=True)
        elif par=='dw':
            p = p.groupby(['DOW']).agg({'products':np.sum,
                                                'GBP_cost':np.mean,
                                                'GBP_products':np.mean,
                                                'GBP_shipping':np.mean,
                                                'GBP_paid':np.mean,
                                                }).sort_index(ascending=False)
            p.reset_index(inplace=True)

            p['Y-M'] = p.index
            p['DOW'] = p.index+1
        elif par=='dm':
            p = p.groupby(['D']).agg({'products':np.sum,
                                                'GBP_cost':np.mean,
                                                'GBP_products':np.mean,
                                                'GBP_shipping':np.mean,
                                                'GBP_paid':np.mean,
                                                }).sort_index(ascending=False)
            p.reset_index(inplace=True)

            p['Y-M'] = p.index
            p['D'] = p.index+1

        p['GBP_shipping'] = p['GBP_shipping'].astype(float)
        p['GBP_products'] = p['GBP_products'].astype(float)
        p['GBP_cost'] = p['GBP_cost'].astype(float)

        p['VAT 8pc'] = round(p['GBP_products']*0.08,2)
        p['Gross Margin'] = round(p['GBP_products'] - p['VAT 8pc'] - p['GBP_cost'],2)

        p['GBP_products_e'] = p['GBP_products']
        p['Gross Margin_e'] = p['Gross Margin']

        if par=='y':
            p.loc[p.index[0],'GBP_products_e'] = round(p.loc[p.index[0],'GBP_products']*365/p.loc[p.index[0],'DOY'],2)
            p.loc[p.index[0],'Gross Margin_e'] = round(p.loc[p.index[0],'Gross Margin']*365/p.loc[p.index[0],'DOY'],2)
        elif par=='m':
            p.loc[p.index[0],'GBP_products_e'] = round(p.loc[p.index[0],'GBP_products']*30/p.loc[p.index[0],'D'],2)
            p.loc[p.index[0],'Gross Margin_e'] = round(p.loc[p.index[0],'Gross Margin']*30/p.loc[p.index[0],'D'],2)
        elif par=='q':
            m = p.loc[p.index[0],'M']%3-1
            print('m',m)
            p.loc[p.index[0],'GBP_products_e'] = round(p.loc[p.index[0],'GBP_products']*90 /
                    (p.loc[p.index[0],'D']+(m)*30),2)
            p.loc[p.index[0],'Gross Margin_e'] = round(p.loc[p.index[0],'Gross Margin']*90 /
                    (p.loc[p.index[0],'D']+(m)*30),2)

        elif par=='d':
            p['GBP_products_e'] = p['GBP_products'].rolling(7).mean()
            p['Gross Margin_e'] = p['Gross Margin'].rolling(7).mean()

            p.sort_index(ascending=False,inplace=True)
            p.reset_index(inplace=True)

            p = p[0:30]

        elif par=='dw' or par=='dm':
            p['GBP_products'] = round(p['GBP_products'],2)
            p['GBP_products_e'] = p['GBP_products'] - p['Gross Margin']

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

