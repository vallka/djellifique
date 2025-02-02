import numpy as np
import pandas as pd
import os
import time
from icecream import ic

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
            #'date_add':'M',
            'date_add':'datetime64[s]',
            'products':'i',
            'orders':'i',
            'GBP_cost':'float64',
            'GBP_products':'float64',
            'GBP_p_exVAT':'float64',
            'GBP_shipping':'float64',
            'GBP_paid':'float64',
        }

    @staticmethod
    def SQL():

        sql = """
SELECT
date(date_add) date_add,
SUM((SELECT SUM(product_quantity) FROM ps17_order_detail d WHERE id_order=o.id_order)) products,
COUNT(id_order) orders,
ROUND((
SUM((SELECT SUM(original_wholesale_price) FROM ps17_order_detail d WHERE id_order=o.id_order)) 
    ),2) GBP_cost
,
ROUND(SUM((total_products_wt-total_discounts_tax_incl)/conversion_rate) ,2) GBP_products,
ROUND(SUM((total_products-total_discounts_tax_excl)/conversion_rate) ,2) GBP_p_exVAT,
ROUND(SUM((total_shipping_tax_incl)/conversion_rate) ,2) GBP_shipping,
ROUND(SUM((total_paid_real)/conversion_rate) ,2) GBP_paid
FROM `ps17_orders` o
WHERE current_state IN
(SELECT id_order_state FROM ps17_order_state WHERE paid=1)
AND NOT EXISTS (SELECT id_order_history FROM ps17_order_history WHERE id_order=o.id_order AND id_order_state IN (29,30))
and date_add>='2020-01-01'
GROUP BY date(date_add)
ORDER BY date_add DESC
        """

        return sql        

    def get_data(par='d',site='uk'):
        store_path = settings.MEDIA_ROOT + f'/{site}' + '/statsdata-v3.pkl'
        
        try:
            tm = os.path.getmtime(store_path) 
            if int(time.time())-int(tm) > 24 * 60 * 60:
                raise Exception("Cache expired")

            p = pd.read_pickle(store_path)
        except Exception as e:
            print (e)
            queryset = DailySalesData.objects.using('presta_eu' if site=='eu' else 'presta').raw(DailySalesData.SQL())
            p = pd.DataFrame(raw_queryset_as_values_list(queryset), columns=list(queryset.columns))
            p = p.astype(DailySalesData.dtypes())

            p['Y'] = p['date_add'].dt.year
            p['M'] = p['date_add'].dt.month
            p['D'] = p['date_add'].dt.day
            p['Q'] = p['date_add'].dt.quarter
            p['DOY'] = p['date_add'].dt.day_of_year
            p['DOW'] = p['date_add'].dt.day_of_week
            p['DIM'] = p['date_add'].dt.days_in_month

            p['VAT 20pc'] = round(p['GBP_products']-p['GBP_p_exVAT'],2)
            p['Gross Margin'] = round(p['GBP_p_exVAT'] - p['GBP_cost'],2)

            p.to_pickle(store_path)

        if par=='y':
            p = p.groupby(['Y',]).agg({'products':np.sum,
                                                'orders':np.sum,
                                                'GBP_cost':np.sum,
                                                'GBP_products':np.sum,
                                                'GBP_p_exVAT':np.sum,
                                                'GBP_shipping':np.sum,
                                                'GBP_paid':np.sum,
                                                'VAT 20pc':np.sum,
                                                'Gross Margin':np.sum,
                                                'DOY':np.max
                                                }).sort_index(ascending=False)
            p['Year'] = p.index
            p.loc[p.index[0],'P estimated'] = round(p.loc[p.index[0],'GBP_products']*365/p.loc[p.index[0],'DOY'],2)
            p.loc[p.index[0],'GM estimated'] = round(p.loc[p.index[0],'Gross Margin']*365/p.loc[p.index[0],'DOY'],2)

        elif par=='q':
            day = p.loc[p.index[0],'D']
            m = (p.loc[p.index[0],'M']-1)%3
            p = p.groupby(['Y','Q']).agg({'products':np.sum,
                                                'orders':np.sum,
                                                'GBP_cost':np.sum,
                                                'GBP_products':np.sum,
                                                'GBP_p_exVAT':np.sum,
                                                'GBP_shipping':np.sum,
                                                'GBP_paid':np.sum,
                                                'VAT 20pc':np.sum,
                                                'Gross Margin':np.sum,
                                                'D':np.max,
                                                'M':np.max
                                                }).sort_index(ascending=False)
            p.reset_index(inplace=True)
            p['Y-M'] = p['Y'].astype(str)+'-'+(1+3*(p['Q'].astype(int)-1)).astype(str)
            p['Quarter'] = p['Y'].astype(str)+'-'+p['Q'].astype(str)

            p.loc[p.index[0],'P estimated'] = round(p.loc[p.index[0],'GBP_products']*91 / (day+(m)*30),2)
            p.loc[p.index[0],'GM estimated'] = round(p.loc[p.index[0],'Gross Margin']*91 / (day+(m)*30),2)

        elif par=='m':
            p = p.groupby(['Y','Q','M']).agg({'products':np.sum,
                                                'orders':np.sum,
                                                'GBP_cost':np.sum,
                                                'GBP_products':np.sum,
                                                'GBP_p_exVAT':np.sum,
                                                'GBP_shipping':np.sum,
                                                'GBP_paid':np.sum,
                                                'VAT 20pc':np.sum,
                                                'Gross Margin':np.sum,
                                                'D':np.max,
                                                'DIM':np.max,
                                                }).sort_index(ascending=False)
            p.reset_index(inplace=True)
            p['Month'] = p['Y'].astype(str)+'-'+p['M'].astype(str)
            p.loc[p.index[0],'P estimated'] = round(p.loc[p.index[0],'GBP_products']*p.loc[p.index[0],'DIM']/p.loc[p.index[0],'D'],2)
            p.loc[p.index[0],'GM estimated'] = round(p.loc[p.index[0],'Gross Margin']*p.loc[p.index[0],'DIM']/p.loc[p.index[0],'D'],2)

        elif par=='d':
            p['Date'] = p['date_add'].astype(str)
            #p.sort_index(ascending=False,inplace=True)
            #p.reset_index(inplace=True)

            #p['P 7day avg'] = p['GBP_products'].rolling(7).mean()
            #p['GM 7day avg'] = p['Gross Margin'].rolling(7).mean()

            #p.sort_index(ascending=False,inplace=True)
            #p.reset_index(inplace=True)
            p = p[0:366]

        elif par=='dw':
            p = p.groupby(['DOW']).agg({'products':np.mean,
                                                'orders':np.mean,
                                                'GBP_cost':np.mean,
                                                'GBP_products':np.mean,
                                                'GBP_p_exVAT':np.mean,
                                                'GBP_shipping':np.mean,
                                                'GBP_paid':np.mean,
                                                'VAT 20pc':np.mean,
                                                'Gross Margin':np.mean,
                                                }).sort_index(ascending=False)
            p.reset_index(inplace=True)

            p['DOW'] = p.index+1
            p['orders'] = round(p['orders'],2)
            p['products'] = round(p['products'],2)
            p['GBP_products'] = round(p['GBP_products'],2)
            p['Gross Margin'] = round(p['Gross Margin'],2)
            p['GBP_products_e'] = p['GBP_products'] - p['Gross Margin']
            p['GBP_p_exVAT'] = round(p['GBP_p_exVAT'],2)
            p['VAT 20pc'] = round(p['VAT 20pc'],2)

        elif par=='dm':
            p = p.groupby(['D']).agg({'products':np.mean,
                                                'orders':np.mean,
                                                'GBP_cost':np.mean,
                                                'GBP_products':np.mean,
                                                'GBP_p_exVAT':np.mean,
                                                'GBP_shipping':np.mean,
                                                'GBP_paid':np.mean,
                                                'VAT 20pc':np.mean,
                                                'Gross Margin':np.mean,
                                                }).sort_index(ascending=False)
            p.reset_index(inplace=True)

            p['Day'] = p.index+1
            p['orders'] = round(p['orders'],2)
            p['products'] = round(p['products'],2)
            p['GBP_products'] = round(p['GBP_products'],2)
            p['Gross Margin'] = round(p['Gross Margin'],2)
            p['GBP_products_e'] = p['GBP_products'] - p['Gross Margin']
            p['GBP_p_exVAT'] = round(p['GBP_p_exVAT'],2)
            p['VAT 20pc'] = round(p['VAT 20pc'],2)


        elif par=='mm':
            p = p.groupby(['M']).agg({'products':np.mean,
                                                'orders':np.mean,
                                                'GBP_cost':np.mean,
                                                'GBP_products':np.mean,
                                                'GBP_p_exVAT':np.mean,
                                                'GBP_shipping':np.mean,
                                                'GBP_paid':np.mean,
                                                'VAT 20pc':np.mean,
                                                'Gross Margin':np.mean,
                                                }).sort_index(ascending=False)
            p.reset_index(inplace=True)

            p['Month'] = p.index+1
            p['orders'] = round(p['orders'],2)
            p['products'] = round(p['products'],2)
            p['GBP_products'] = round(p['GBP_products'],2)
            p['Gross Margin'] = round(p['Gross Margin'],2)
            p['GBP_products_e'] = p['GBP_products'] - p['Gross Margin']
            p['GBP_p_exVAT'] = round(p['GBP_p_exVAT'],2)
            p['VAT 20pc'] = round(p['VAT 20pc'],2)

        elif par=='mavg':
            p1 = p.groupby(['Y','M']).agg({'products':np.sum,
                                                'orders':np.sum,
                                                'GBP_products':np.sum,
                                                'GBP_p_exVAT':np.sum,
                                                'VAT 20pc':np.sum,
                                                'Gross Margin':np.sum,
                                                }).sort_index(ascending=False)
            p2 = p1.groupby(['Y',]).agg({'products':np.mean,
                                                'orders':np.mean,
                                                'GBP_products':np.mean,
                                                'GBP_p_exVAT':np.mean,
                                                'VAT 20pc':np.mean,
                                                'Gross Margin':np.mean,
                                                }).sort_index(ascending=False)
            p2['products'] = round(p2['products'],2)
            p2['orders'] = round(p2['orders'],2)
            p2['GBP_products'] = round(p2['GBP_products'],2)
            p2['GBP_p_exVAT'] = round(p2['GBP_p_exVAT'],2)
            p2['VAT 20pc'] = round(p2['VAT 20pc'],2)
            p2['Gross Margin'] = round(p2['Gross Margin'],2)

            p2.loc['All Time'] = round(p2.mean(),2)

            p2['Year'] = p2.index

            return p2                                                

        elif par=='davg':
            p1 = p.groupby(['Y','M']).agg({'products':np.mean,
                                                'orders':np.mean,
                                                'GBP_products':np.mean,
                                                'GBP_p_exVAT':np.mean,
                                                'VAT 20pc':np.mean,
                                                'Gross Margin':np.mean,
                                                }).sort_index(ascending=False)
            p2 = p1.groupby(['Y',]).agg({'products':np.mean,
                                                'orders':np.mean,
                                                'GBP_products':np.mean,
                                                'GBP_p_exVAT':np.mean,
                                                'VAT 20pc':np.mean,
                                                'Gross Margin':np.mean,

                                                }).sort_index(ascending=False)
            p2['products'] = round(p2['products'],2)
            p2['orders'] = round(p2['orders'],2)
            p2['GBP_products'] = round(p2['GBP_products'],2)
            p2['GBP_p_exVAT'] = round(p2['GBP_p_exVAT'],2)
            p2['VAT 20pc'] = round(p2['VAT 20pc'],2)
            p2['Gross Margin'] = round(p2['Gross Margin'],2)
            
            p2.loc['All Time'] = round(p2.mean(),2)
            p2['Year'] = p2.index

            return p2                                                

        return p

class MonthlyCustomersData(models.Model):
    month = models.CharField(primary_key=True,max_length=20)

    @staticmethod
    def SQL(par='m'):

        sbstr = 4 if par == 'y' else 7

        sql = f"""
SELECT 
SUBSTR(DATE_ADD,1,{sbstr}) month ,
COUNT(DISTINCT id_customer) customers,

(SELECT
COUNT(DISTINCT id_customer)
FROM `ps17_orders` o1
WHERE current_state IN
(SELECT id_order_state FROM ps17_order_state WHERE paid=1)
AND YEAR(DATE_ADD)=YEAR(o.date_add)
AND (MONTH(DATE_ADD)=MONTH(o.date_add) or '{par}'='y')
AND NOT EXISTS(SELECT id_order FROM ps17_orders o2 WHERE o1.id_customer=o2.id_customer AND 
o2.current_state IN        (SELECT id_order_state FROM ps17_order_state WHERE paid=1) AND 
o2.date_add<o1.date_add
)) new_customers,

COUNT(id_order) orders,

(SELECT
COUNT(DISTINCT id_order)
FROM `ps17_orders` o1
WHERE current_state IN
(SELECT id_order_state FROM ps17_order_state WHERE paid=1)
AND YEAR(DATE_ADD)=YEAR(o.date_add)
AND (MONTH(DATE_ADD)=MONTH(o.date_add) or '{par}'='y')
AND NOT EXISTS(SELECT id_order FROM ps17_orders o2 WHERE o1.id_customer=o2.id_customer AND 
o2.current_state IN        (SELECT id_order_state FROM ps17_order_state WHERE paid=1) AND 
o2.date_add<o1.date_add
)) new_orders,

SUM((total_products_wt-total_discounts_tax_incl)/conversion_rate) sales,

(SELECT
SUM((total_products_wt-total_discounts_tax_incl)/conversion_rate)
FROM `ps17_orders` o1
WHERE current_state IN
(SELECT id_order_state FROM ps17_order_state WHERE paid=1)
AND YEAR(DATE_ADD)=YEAR(o.date_add)
AND (MONTH(DATE_ADD)=MONTH(o.date_add) or '{par}'='y')
AND NOT EXISTS(SELECT id_order FROM ps17_orders o2 WHERE o1.id_customer=o2.id_customer AND 
o2.current_state IN        (SELECT id_order_state FROM ps17_order_state WHERE paid=1) AND 
o2.date_add<o1.date_add
)) new_sales,

(SELECT
COUNT(id_customer)
FROM ps17_customer c
WHERE 
YEAR(c.date_add)=YEAR(o.date_add)
AND (MONTH(DATE_ADD)=MONTH(o.date_add) or '{par}'='y')
) registrations,

(SELECT
COUNT(id_customer)
FROM ps17_customer c
WHERE 
YEAR(c.date_add)=YEAR(o.date_add)
AND (MONTH(DATE_ADD)=MONTH(o.date_add) or '{par}'='y')
AND EXISTS(SELECT id_order FROM ps17_orders o2 WHERE c.id_customer=o2.id_customer AND 
o2.current_state IN        (SELECT id_order_state FROM ps17_order_state WHERE paid=1)
)) registrations_customers

FROM `ps17_orders` o
WHERE current_state IN
(SELECT id_order_state FROM ps17_order_state WHERE paid=1)
and date_add>='2021-01-01'

GROUP BY SUBSTR(DATE_ADD,1,{sbstr}) 
ORDER BY 1 DESC

        """
        
        return sql        

    @staticmethod
    def dtypes():
        return {
            'customers':'i',
            'new_customers':'i',
            'orders':'i',
            'new_orders':'i',
            'sales':'float64',
            'new_sales':'float64',
            'registrations':'i',
            'registrations_customers':'i',
        }

    @classmethod
    def get_data(cls,par='m',site='uk'):
        print('par',par)
        store_path = settings.MEDIA_ROOT  + f'/{site}' + f'/stats-customers-data-{par}-v1.pkl'
        
        try:
            tm = os.path.getmtime(store_path) 
            if int(time.time())-int(tm) > 24 * 60 * 60:
                raise Exception("Cache expired")

            p = pd.read_pickle(store_path)
        except Exception as e:
            print (e)
            print(cls.SQL(par))
            queryset = cls.objects.using('presta_eu' if site=='eu' else 'presta').raw(cls.SQL(par))
            p = pd.DataFrame(raw_queryset_as_values_list(queryset), columns=list(queryset.columns))
            p = p.astype(cls.dtypes())

            p['sales'] = round(p['sales'],2)
            p['new_sales'] = round(p['new_sales'],2)

            p['%nc'] = round(p['new_customers']*100/p['customers'],1)
            p['%no'] = round(p['new_orders']*100/p['orders'],1)
            p['%ns'] = round(p['new_sales']*100/p['sales'],1)

            p.to_pickle(store_path)

        return p

class MonthlyTotalCustomersData(models.Model):
    year_mon = models.CharField(primary_key=True,max_length=20)

    @staticmethod
    def SQL():

        sql = """
SELECT ccc.*
,

IF (DATE_FORMAT(DATE_SUB(NOW(),INTERVAL 3 MONTH),'%%Y-%%m')>=year_mon,
(SELECT
COUNT(DISTINCT id_customer)
FROM `ps17_orders` o1
WHERE current_state IN
(SELECT id_order_state FROM ps17_order_state WHERE paid=1)
AND
DATE_FORMAT(o1.date_add,'%%Y-%%m')=year_mon
AND NOT EXISTS(SELECT id_order FROM ps17_orders o2 WHERE o1.id_customer=o2.id_customer AND 
o2.current_state IN        (SELECT id_order_state FROM ps17_order_state WHERE paid=1) AND 
DATE_FORMAT(o2.date_add,'%%Y-%%m')>year_mon
)
)
,NULL
) lost_customers

FROM
(
SELECT year_mon,COUNT(id_customer) new_customers,SUM(live) live_customers_mon 
FROM
(
SELECT c.id_customer,
DATE_FORMAT(MIN(o.date_add),'%%Y-%%m') year_mon, 
MAX(o.date_add),

IF(MAX(o.date_add)>DATE_SUB(NOW(),INTERVAL 3 MONTH),1,0) live

FROM ps17_customer c
JOIN ps17_orders o ON o.id_customer = c.id_customer AND o.current_state IN (SELECT id_order_state FROM ps17_order_state WHERE paid=1) 
WHERE ACTIVE=1 AND deleted=0
GROUP BY c.id_customer
ORDER BY year_mon
) cc
GROUP BY year_mon
ORDER BY year_mon
) ccc        """
        
        return sql        

    @staticmethod
    def dtypes():
        return {
            'new_customers':'i',
            'live_customers_mon':'i',
        }

    @classmethod
    def get_data(cls,par='t',site='uk'):
        print('par',par)
        store_path = settings.MEDIA_ROOT  + f'/{site}' + f'/stats-customers-data-{par}-v1.pkl'
        
        try:
            tm = os.path.getmtime(store_path) 
            if int(time.time())-int(tm) > 24 * 60 * 60:
            #if int(time.time())-int(tm) > 1:
                raise Exception("Cache expired")

            p = pd.read_pickle(store_path)
        except Exception as e:
            print (e)
            print(cls.SQL())
            queryset = cls.objects.using('presta_eu' if site=='eu' else 'presta').raw(cls.SQL())
            p = pd.DataFrame(raw_queryset_as_values_list(queryset), columns=list(queryset.columns))
            p = p.astype(cls.dtypes())

            p['total_customers'] = p['new_customers'].cumsum()
            p['live_customers'] = p['live_customers_mon'].cumsum()
            #p['new_customers_year'] = p['new_customers'].rolling(12).sum()
            p.sort_index(ascending=False,inplace=True)

            p.to_pickle(store_path)

        return p

class CustomersBehaviourData(models.Model):
    id_customer = models.IntegerField(primary_key=True)

    @staticmethod
    def SQL():

        sql = """
SELECT cc.* ,
total_gbp/orders avg_order_gbp,
IF (orders>1,round(DATEDIFF(order_last,order_first)/orders,0),NULL) orders_apart_days,
IF (orders>1,DATE_ADD(order_last,INTERVAL DATEDIFF(order_last,order_first)/orders DAY),NULL) order_due,
IF (orders>1,DATEDIFF(NOW(),DATE_ADD(order_last,INTERVAL DATEDIFF(order_last,order_first)/orders DAY)),NULL) order_missed,
(SELECT DATE(MAX(ca.date_upd)) FROM ps17_cart ca WHERE ca.id_customer=cc.id_customer) last_cart
FROM
(
SELECT DISTINCT
 c.id_customer, CONCAT(c.firstname,' ',c.lastname) customer_name,
 c.id_default_group,
 (SELECT NAME FROM ps17_group_lang WHERE id_lang=1 AND id_group=c.id_default_group) "group",

(SELECT COUNT(id_order)FROM ps17_orders o1 WHERE 
o1.id_customer=c.id_customer
AND current_state IN
(SELECT id_order_state FROM ps17_order_state WHERE paid=1)) orders,

(SELECT MIN(DATE(DATE_ADD)) FROM ps17_orders o1 WHERE 
o1.id_customer=c.id_customer
AND current_state IN
(SELECT id_order_state FROM ps17_order_state WHERE paid=1)) order_first,

(SELECT MAX(DATE(DATE_ADD)) FROM ps17_orders o1 WHERE 
o1.id_customer=c.id_customer
AND current_state IN
(SELECT id_order_state FROM ps17_order_state WHERE paid=1)) order_last,

(SELECT
SUM((total_products_wt-total_discounts_tax_incl)/conversion_rate) FROM ps17_orders o1 WHERE 
o1.id_customer=c.id_customer
AND current_state IN
(SELECT id_order_state FROM ps17_order_state WHERE paid=1)) total_gbp
 
FROM ps17_orders o JOIN ps17_customer c ON o.id_customer=c.id_customer
WHERE current_state IN
(SELECT id_order_state FROM ps17_order_state WHERE paid=1)
ORDER BY 1
) cc
WHERE orders>0 
        """
        
        return sql        

    @staticmethod
    def dtypes():
        return {
            'id_customer':'i',
            'id_default_group':'i',
            'orders':'i',
            #'order_first':'M',
            #'order_last':'M',
            #'order_due':'M',
            'order_first':'datetime64[s]',
            'order_last':'datetime64[s]',
            'order_due':'datetime64[s]',
            'total_gbp':'f',
            'avg_order_gbp':'f',
            'orders_apart_days':'f',
            'order_missed':'f',
            #'last_cart':'M',
            'last_cart':'datetime64[s]',
        }

    @classmethod
    def get_data(cls,par='c',site='uk'):
        print('par',par)
        store_path = settings.MEDIA_ROOT  + f'/{site}' + f'/stats-customers-behaviour-v2.pkl'
        
        try:
            tm = os.path.getmtime(store_path) 
            if int(time.time())-int(tm) > 24 * 60 * 60:
                raise Exception("Cache expired")

            p = pd.read_pickle(store_path)
        except Exception as e:
            print (e)
            print(cls.SQL())
            queryset = cls.objects.using('presta_eu' if site=='eu' else 'presta').raw(cls.SQL())
            p = pd.DataFrame(raw_queryset_as_values_list(queryset), columns=list(queryset.columns))
            p = p.astype(cls.dtypes())

            p.to_pickle(store_path)

        if par=='g':
            p['avg_orders'] = p['orders']
            p = p.groupby(['group',]).agg({'id_customer':'count',
                                                'orders':np.sum,
                                                'avg_orders':np.mean,
                                                'total_gbp':np.sum,
                                                'avg_order_gbp':np.mean,
                                                'orders_apart_days':np.mean,
                                                'order_first':np.min,
                                                'order_last':np.max,
                                                }).sort_index()

            p['group'] = p.index
            print(p)                                            


        return p

class ProductsData(models.Model):
    id_product = models.IntegerField(primary_key=True)

    @staticmethod
    def SQL():
        sql = """
SELECT aa.product_id,pp.id_product,product_reference,product_name,
aa.quantity sold, min_date,max_date,

(SELECT COUNT(*) FROM ps17_category_product WHERE id_product=aa.product_id AND id_category=18) bt,
(SELECT COUNT(*) FROM ps17_category_product WHERE id_product=aa.product_id AND id_category=105) gelclr,
(SELECT COUNT(*) FROM ps17_category_product WHERE id_product=aa.product_id AND id_category=150) procare,
(SELECT COUNT(*) FROM ps17_category_product WHERE id_product=aa.product_id AND id_category=156) soakoff,
(SELECT COUNT(*) FROM ps17_category_product WHERE id_product=aa.product_id AND id_category=157) fileoff,
(SELECT COUNT(*) FROM ps17_category_product WHERE id_product=aa.product_id AND id_category=78) acry,
(SELECT COUNT(*) FROM ps17_category_product WHERE id_product=aa.product_id AND id_category=111) qt,
(SELECT COUNT(*) FROM ps17_category_product WHERE id_product=aa.product_id AND id_category=21) outlet,
(SELECT COUNT(*) FROM ps17_category_product WHERE id_product=aa.product_id AND id_category=153) archive

FROM 
(
SELECT product_id,SUM(product_quantity) quantity,product_name ,product_reference,
MAX(DATE(DATE_ADD)) max_date,
MIN(DATE(DATE_ADD)) min_date
FROM
(
SELECT o.id_order, d.product_id,d.product_quantity,DATE_ADD,d.product_name,d.product_reference 
FROM `ps17_orders` o JOIN ps17_order_detail d ON d.id_order=o.id_order
WHERE current_state IN (SELECT id_order_state FROM ps17_order_state WHERE paid=1)

) a
GROUP BY product_id    
) aa
LEFT OUTER JOIN ps17_product pp ON pp.id_product=aa.product_id
ORDER BY aa.quantity DESC
"""
        
        return sql        

    @staticmethod
    def dtypes():
        return {
            'id_product':'f',
            'sold':'i',
            #'min_date':'M',
            #'max_date':'M',
            'min_date':'datetime64[s]',
            'max_date':'datetime64[s]',
            'bt':'i',
            'gelclr':'i',	
            'procare':'i',	
            'soakoff':'i',	
            'fileoff':'i',	
            'acry':'i',	
            'qt':'i',
            'outlet':'i',
            'archive':'i',
        }

    @classmethod
    def get_data(cls,par='c',site='uk'):
        print('par',par)
        store_path = settings.MEDIA_ROOT  + f'/{site}' + f'/stats-products-v4.pkl'
        
        try:
            tm = os.path.getmtime(store_path) 
            if int(time.time())-int(tm) > 24 * 60 * 60:
                raise Exception("Cache expired")

            p = pd.read_pickle(store_path)
        except Exception as e:
            print (e)
            print(cls.SQL())
            queryset = cls.objects.using('presta_eu' if site=='eu' else 'presta').raw(cls.SQL())
            p = pd.DataFrame(raw_queryset_as_values_list(queryset), columns=list(queryset.columns))
            p = p.astype(cls.dtypes())

            p['product_name'] = p['product_name'].str.upper()
            p['product_name'] = p['product_name'].str.replace(r' \(HEMA FREE\)','')
            p['product_name'] = p['product_name'].str.replace(r'^\d\.\s*','')
            p['product_name'] = p['product_name'].str.replace(r'^P\d\d\s*','')
            p['product_name'] = p['product_name'].str.replace(r'^PASTEL\s*-\s*','')
            p['product_name'] = p['product_name'].str.replace(r'^PASTEL 2020\s*-\s*','')
            p['product_name'] = p['product_name'].str.replace(r'"',' ')
            p['product_name'] = p['product_name'].str.replace(r'-',' ')
            p['product_name'] = p['product_name'].str.replace(r'\(',' ')
            p['product_name'] = p['product_name'].str.replace(r'\)',' ')
            p['product_name'] = p['product_name'].str.replace(r'\s+',' ')
            p['product_name'] = p['product_name'].str.replace(r'BASE COAT','BASE')
            p['product_name'] = p['product_name'].str.replace(r'TOP COAT','TOP')
            p['product_name'] = p['product_name'].str.replace(r'DRY TOP','TOP')
            
            p['product_name'] = p['product_name'].str.strip()
            
            
            p = p.groupby(['product_name',]).agg({'id_product':np.min,
                                                'sold':np.sum,
                                                'min_date':np.min,
                                                'max_date':np.max,
                                                'bt':np.max,
                                                'gelclr':np.max,	
                                                'procare':np.max,	
                                                'soakoff':np.max,	
                                                'fileoff':np.max,	
                                                'acry':np.max,	
                                                'qt':np.max,
                                                'outlet':np.max,
                                                'archive':np.max,
                                                })

            #p['months_in_sale'] = (p['max_date'].astype('M')-p['min_date'].astype('M'))/np.timedelta64(1,'M')
            p['months_in_sale'] = (p['max_date'].astype('datetime64[s]')-p['min_date'].astype('datetime64[s]'))/(np.timedelta64(1,'s')*30.44 * 24 * 60 * 60)
            p['per_month'] = p['sold'] / p['months_in_sale']
            p.loc[p['months_in_sale']==0,'per_month']=0

            p['name'] = p.index

            #p.loc[p['name'].str.contains('APEX'),'apex']=1
            #p.loc[p['name'].str.contains('QUICK TIPS'),'qt']=1
            #p.loc[p['name'].str.contains('BUILDER GEL'),'hb']=1
            #p.loc[p['name'].str.contains('ACRYLIC GEL'),'acry']=1
            #p.loc[p['name'].str.contains('PRIMER'),'bt']=1
            p.loc[p['name'].str.contains('MATTE TOP'),'bt']=1
            p.loc[p['name'].str.contains('RUBBER TOP'),'bt']=1
            p.loc[p['name'].str.contains('RUBBER BASE'),'bt']=1
            p.loc[p['name'].str.contains('MICROCRYSTAL BASE'),'bt']=1
            p.loc[p['name'].str.contains('PRO BASE'),'bt']=1
            

            p.to_pickle(store_path)

        return p

class StockData(models.Model):
    id = models.IntegerField(primary_key=True)

    @staticmethod
    def SQL():
        sql = """
        select id,concat_ws('-',id_product,if(id_product_attribute=0,null,(
        select name
        from ps17_product_attribute_combination ac join ps17_attribute_lang al on id_lang=1 and ac.id_attribute=al.id_attribute
        where id_product_attribute=aa.id_product_attribute)
        )) as id_product
        ,concat_ws(': ',reference,if(id_product_attribute=0,
        (select name from ps17_product_lang where id_product=aa.id_product and id_lang=1 and id_shop=1),
        (
        select name
        from ps17_product_attribute_combination ac join ps17_attribute_lang al on id_lang=1 and ac.id_attribute=al.id_attribute
        where id_product_attribute=aa.id_product_attribute)
        )) as reference
        ,qnt,date_add,
        (select count(*) from ps17_category_product where id_product=aa.id_product and id_category=18) bt,
        (select count(*) from ps17_category_product where id_product=aa.id_product and id_category=105) gelclr,
        (select count(*) from ps17_category_product where id_product=aa.id_product and id_category=150) procare,
        (select count(*) from ps17_category_product where id_product=aa.id_product and id_category=156) soakoff,
        (select count(*) from ps17_category_product where id_product=aa.id_product and id_category=157) fileoff,
        (select count(*) from ps17_category_product where id_product=aa.id_product and id_category=78) acry,
        (select count(*) from ps17_category_product where id_product=aa.id_product and id_category=111) qt,
        (select count(*) from ps17_category_product where id_product=aa.id_product and id_category=21) outlet,
        (select count(*) from ps17_category_product where id_product=aa.id_product and id_category=153) archive
        from a_stock_history aa
        where date_add>=date_sub(now(),interval 6 month)
        and id_product in (select id_product from ps17_product_shop where id_shop=1 and active=1)
        and id_product not in (select id_product from ps17_category_product where id_category=123)        
        order by id"""
        return sql        

    @staticmethod
    def dtypes():
        return {
            'id':'i',
            'id_product':'str',
            'qnt':'i',
            #'date_add':'M',
            'date_add':'datetime64[s]',
            'bt':'i',
            'gelclr':'i',	
            'procare':'i',	
            'soakoff':'i',	
            'fileoff':'i',	
            'acry':'i',	
            'qt':'i',
            'outlet':'i',
            'archive':'i',
        }

    @classmethod
    def get_data(cls,par='*',site='uk'):
        #ic('par',par)
        store_path =  settings.MEDIA_ROOT  + f'/{site}' + f'/stats-stock-v2.pkl'
        
        try:
            tm = os.path.getmtime(store_path) 
            if int(time.time())-int(tm) > 24 * 60 * 60:
                raise Exception("Cache expired")

            p = pd.read_pickle(store_path)
        except Exception as e:
            ic (e)
            ic(cls.SQL())
            queryset = cls.objects.using('presta_eu' if site=='eu' else 'presta').raw(cls.SQL())
            p = pd.DataFrame(raw_queryset_as_values_list(queryset), columns=list(queryset.columns))
            p = p.astype(cls.dtypes())

            #print (p[:10])
            p.to_pickle(store_path)
            
        if par!='*':
            store_path = settings.MEDIA_ROOT  + f'/{site}' + f'/stats-stock-{par}-v1.pkl'

            try:
                tm = os.path.getmtime(store_path) 
                if int(time.time())-int(tm) > 24 * 60 * 60:
                    raise Exception("Cache expired")

                p = pd.read_pickle(store_path)            
            except Exception as e:
                ic (e)
                p=p[p['id_product']==par]
                q=None
                refill=None
                p0=None
                date_out = None
                for i in p.index:
                    if not date_out and p.at[i,'qnt']<=0:
                        date_out = p.at[i,'date_add']
                    if i>0 and i<max(p.index) and p.at[i,'qnt']==q:
                        p.at[i,'qnt'] = None
                    else:
                        if q!=None and q<p.at[i,'qnt']:
                            #print('<<<',i)
                            refill=i
                            date_out = None

                        q = p.at[i,'qnt']
                        p.at[i,'qnt2']=q

                if refill:
                    p0=p[p.index<refill]  
                    p0.reset_index(inplace=True)
                    p0=p0[np.isfinite(p0['qnt'])]
                    p=p[p.index>=refill]        

                p.reset_index(inplace=True)
                first_dt=min(p['date_add'])
                p['index'] = (p['date_add']-first_dt).dt.days

                p=p[np.isfinite(p['qnt'])]

                d = np.polyfit(p['index'],p['qnt'],1)
                f = np.poly1d(d)

                last_dt=max(p['date_add'])
                last_ix=max(p['index'])           

                p['predicton']=f(p['index'])
                if date_out: p['date_out'] = date_out

                already_out = (p.iloc[-1]['qnt']<=0)

                if not already_out:
                    last_adj = p.iloc[-1]['qnt']-p.iloc[-1]['predicton']
                    p=p.append({'date_add':last_dt+pd.DateOffset(days=1),
                                        'index':last_ix+1,'reference':p.iloc[-1]['reference'],'predicton':f(last_ix+1)+last_adj,},ignore_index=True)

                    for i in range(2,191):
                        if f(last_ix+i)+last_adj>=0:
                            pass
                        else:
                            p=p.append({'date_add':last_dt+pd.DateOffset(days=i),
                                        'index':last_ix+i,'qnt':0,'reference':p.iloc[-1]['reference'],'predicton':f(last_ix+i)+last_adj,'getting_out':True},ignore_index=True)
                            break;

                    if i>=190:
                        p=p.append({'date_add':last_dt+pd.DateOffset(days=i),
                                    'index':last_ix+i,'predicton':f(last_ix+i),'reference':p.iloc[-1]['reference'],'getting_out':False},ignore_index=True)

                #else:
                #    i = 2
                #    p=p.append({'date_add':last_dt+pd.DateOffset(days=i),
                #                'index':last_ix+i,'predicton':f(last_ix+i),'reference':int(f(last_ix+i)),},ignore_index=True)
                
                if refill:
                    p=p0.append(p,ignore_index=True)
                    #print (p)

            p.to_pickle(store_path)

        return p
