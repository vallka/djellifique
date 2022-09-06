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
ROUND(SUM((total_shipping_tax_incl)/conversion_rate) ,2) GBP_shipping,
ROUND(SUM((total_paid_real)/conversion_rate) ,2) GBP_paid
FROM `ps17_orders` o
WHERE current_state IN
(SELECT id_order_state FROM ps17_order_state WHERE paid=1)
AND NOT EXISTS (SELECT id_order_history FROM ps17_order_history WHERE id_order=o.id_order AND id_order_state IN (29,30))
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
            day = p.loc[p.index[0],'D']
            m = (p.loc[p.index[0],'M']-1)%3
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

            p.loc[p.index[0],'P estimated'] = round(p.loc[p.index[0],'GBP_products']*91 / (day+(m)*30),2)
            p.loc[p.index[0],'GM estimated'] = round(p.loc[p.index[0],'Gross Margin']*91 / (day+(m)*30),2)

        elif par=='m':
            p = p.groupby(['Y','Q','M']).agg({'products':np.sum,
                                                'orders':np.sum,
                                                'GBP_cost':np.sum,
                                                'GBP_products':np.sum,
                                                'GBP_shipping':np.sum,
                                                'GBP_paid':np.sum,
                                                'VAT 8pc':np.sum,
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
SUBSTR(o2.date_add,1,{sbstr})<SUBSTR(o1.date_add,1,{sbstr})
)) new_customers,

(SELECT
COUNT(DISTINCT id_customer)
FROM `ps17_orders` o1
WHERE current_state IN
(SELECT id_order_state FROM ps17_order_state WHERE paid=1)
AND YEAR(DATE_ADD)=YEAR(o.date_add)
AND (MONTH(DATE_ADD)=MONTH(o.date_add) or '{par}'='y')
AND NOT EXISTS(SELECT id_order FROM ps17_orders o2 WHERE o1.id_customer=o2.id_customer AND
o2.current_state IN        (SELECT id_order_state FROM ps17_order_state WHERE paid=1) AND
SUBSTR(o2.date_add,1,{sbstr})>SUBSTR(o1.date_add,1,{sbstr})
)) last_customers,

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
SUBSTR(o2.date_add,1,{sbstr})<SUBSTR(o1.date_add,1,{sbstr})
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
SUBSTR(o2.date_add,1,{sbstr})<SUBSTR(o1.date_add,1,{sbstr})
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
and date_add>='2019-01-01'

GROUP BY SUBSTR(DATE_ADD,1,{sbstr}) 
ORDER BY 1 DESC

        """
        
        return sql        

    @staticmethod
    def dtypes():
        return {
            'customers':'i',
            'new_customers':'i',
            'last_customers':'i',
            'orders':'i',
            'new_orders':'i',
            'sales':'float64',
            'new_sales':'float64',
            'registrations':'i',
            'registrations_customers':'i',
        }

    @classmethod
    def get_data(cls,par='m'):
        print('par',par)
        store_path = settings.MEDIA_ROOT + f'/stats-customers-data-{par}-v1.pkl'
        
        try:
            tm = os.path.getmtime(store_path) 
            if int(time.time())-int(tm) > 24 * 60 * 60:
                raise Exception("Cache expired")

            p = pd.read_pickle(store_path)
        except Exception as e:
            print (e)
            print(cls.SQL(par))
            queryset = cls.objects.using('presta').raw(cls.SQL(par))
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
    month = models.CharField(primary_key=True,max_length=20)

    @staticmethod
    def SQL():

        sql = """
SELECT month ,

(SELECT
COUNT(DISTINCT id_customer)
FROM `ps17_orders` o1
WHERE current_state IN
(SELECT id_order_state FROM ps17_order_state WHERE paid=1)
AND
SUBSTR(o1.date_add,1,7)<=oo.month
) total_customers,

(SELECT
COUNT(DISTINCT id_customer)
FROM `ps17_orders` o1
WHERE current_state IN
(SELECT id_order_state FROM ps17_order_state WHERE paid=1)
AND
SUBSTR(o1.date_add,1,7)<=oo.month
AND EXISTS(SELECT id_order FROM ps17_orders o2 WHERE o1.id_customer=o2.id_customer AND 
o2.current_state IN        (SELECT id_order_state FROM ps17_order_state WHERE paid=1) AND 
SUBSTR(o2.date_add,1,7)>oo.month
)) loyal_customers

FROM
(
SELECT 
SUBSTR(DATE_ADD,1,7) month 
FROM ps17_orders o
WHERE DATE(DATE_ADD)>='2019-01-01'
GROUP BY SUBSTR(DATE_ADD,1,7)
ORDER BY 1 DESC
) oo
        """
        
        return sql        

    @staticmethod
    def dtypes():
        return {
            'total_customers':'i',
            'loyal_customers':'i',
        }

    @classmethod
    def get_data(cls,par='t'):
        print('par',par)
        store_path = settings.MEDIA_ROOT + f'/stats-customers-data-{par}-v1.pkl'
        
        try:
            tm = os.path.getmtime(store_path) 
            if int(time.time())-int(tm) > 24 * 60 * 60:
                raise Exception("Cache expired")

            p = pd.read_pickle(store_path)
        except Exception as e:
            print (e)
            print(cls.SQL())
            queryset = cls.objects.using('presta').raw(cls.SQL())
            p = pd.DataFrame(raw_queryset_as_values_list(queryset), columns=list(queryset.columns))
            p = p.astype(cls.dtypes())

            p.to_pickle(store_path)

        return p

class CustomersBehaviourData(models.Model):
    id_customer = models.IntegerField(primary_key=True)

    @staticmethod
    def SQL():

        sql = """
SELECT cc.* ,
total_gbp/orders avg_order_gbp,
IF (orders>1,DATEDIFF(order_last,order_first)/orders,NULL) orders_apart_days
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
            'order_first':'M',
            'order_last':'M',
            'total_gbp':'f',
            'avg_order_gbp':'f',
            'orders_apart_days':'f',
        }

    @classmethod
    def get_data(cls,par='c'):
        print('par',par)
        store_path = settings.MEDIA_ROOT + f'/stats-customers-behaviour-v2.pkl'
        
        try:
            tm = os.path.getmtime(store_path) 
            if int(time.time())-int(tm) > 24 * 60 * 60:
                raise Exception("Cache expired")

            p = pd.read_pickle(store_path)
        except Exception as e:
            print (e)
            print(cls.SQL())
            queryset = cls.objects.using('presta').raw(cls.SQL())
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
(SELECT COUNT(*) FROM ps17_category_product WHERE id_product=aa.product_id AND id_category=60) gelclr,
(SELECT COUNT(*) FROM ps17_category_product WHERE id_product=aa.product_id AND id_category=78) acry,
(SELECT COUNT(*) FROM ps17_category_product WHERE id_product=aa.product_id AND id_category=79) hb,
(SELECT COUNT(*) FROM ps17_category_product WHERE id_product=aa.product_id AND id_category=87) apex,
(SELECT COUNT(*) FROM ps17_category_product WHERE id_product=aa.product_id AND id_category=111) qt
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
            'min_date':'M',
            'max_date':'M',
            'bt':'i',
            'gelclr':'i',	
            'acry':'i',	
            'hb':'i',	
            'apex':'i',	
            'qt':'i',
        }

    @classmethod
    def get_data(cls,par='c'):
        print('par',par)
        store_path = settings.MEDIA_ROOT + f'/stats-products-v3.pkl'
        
        try:
            tm = os.path.getmtime(store_path) 
            if int(time.time())-int(tm) > 24 * 60 * 60:
                raise Exception("Cache expired")

            p = pd.read_pickle(store_path)
        except Exception as e:
            print (e)
            print(cls.SQL())
            queryset = cls.objects.using('presta').raw(cls.SQL())
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
                                                'acry':np.max,	
                                                'hb':np.max,	
                                                'apex':np.max,	
                                                'qt':np.max,
                                                })

            p['months_in_sale'] = (p['max_date'].astype('M')-p['min_date'].astype('M'))/np.timedelta64(1,'M')
            p['per_month'] = p['sold'] / p['months_in_sale']
            p.loc[p['months_in_sale']==0,'per_month']=0

            p['name'] = p.index

            p.loc[p['name'].str.contains('APEX'),'apex']=1
            p.loc[p['name'].str.contains('QUICK TIPS'),'qt']=1
            p.loc[p['name'].str.contains('BUILDER GEL'),'hb']=1
            p.loc[p['name'].str.contains('ACRYLIC GEL'),'acry']=1
            p.loc[p['name'].str.contains('PRIMER'),'bt']=1
            p.loc[p['name'].str.contains('MATTE TOP'),'bt']=1
            p.loc[p['name'].str.contains('RUBBER TOP'),'bt']=1
            p.loc[p['name'].str.contains('RUBBER BASE'),'bt']=1
            p.loc[p['name'].str.contains('PRO BASE'),'bt']=1
            

            p.to_pickle(store_path)

        return p

class StockData(models.Model):
    id = models.IntegerField(primary_key=True)

    @staticmethod
    def SQL():
        sql = """
        SELECT id,id_product,reference,qnt,date_add,
        (SELECT COUNT(*) FROM ps17_category_product WHERE id_product=aa.id_product AND id_category=18) bt,
        (SELECT COUNT(*) FROM ps17_category_product WHERE id_product=aa.id_product AND id_category=60) gelclr,
        (SELECT COUNT(*) FROM ps17_category_product WHERE id_product=aa.id_product AND id_category=78) acry,
        (SELECT COUNT(*) FROM ps17_category_product WHERE id_product=aa.id_product AND id_category=79) hb,
        (SELECT COUNT(*) FROM ps17_category_product WHERE id_product=aa.id_product AND id_category=87) apex,
        (SELECT COUNT(*) FROM ps17_category_product WHERE id_product=aa.id_product AND id_category=111) qt        
        FROM a_stock_history aa
        order by id
"""

        return sql        

    @staticmethod
    def dtypes():
        return {
            'id':'i',
            'id_product':'i',
            'qnt':'i',
            'date_add':'M',
            'bt':'i',
            'gelclr':'i',	
            'acry':'i',	
            'hb':'i',	
            'apex':'i',	
            'qt':'i',
        }

    @classmethod
    def get_data(cls,par='*'):
        print('par',par)
        store_path = settings.MEDIA_ROOT + f'/stats-stock-v1.pkl'
        
        try:
            tm = os.path.getmtime(store_path) 
            if int(time.time())-int(tm) > 24 * 60 * 60:
                raise Exception("Cache expired")

            p = pd.read_pickle(store_path)
        except Exception as e:
            print (e)
            print(cls.SQL())
            queryset = cls.objects.using('presta').raw(cls.SQL())
            p = pd.DataFrame(raw_queryset_as_values_list(queryset), columns=list(queryset.columns))
            p = p.astype(cls.dtypes())

            #print (p[:10])
            p.to_pickle(store_path)
            
        if par!='*':
            store_path = settings.MEDIA_ROOT + f'/stats-stock-{par}-v1.pkl'

            try:
                tm = os.path.getmtime(store_path) 
                if int(time.time())-int(tm) > 24 * 60 * 60:
                    raise Exception("Cache expired")

                p = pd.read_pickle(store_path)            
            except Exception as e:
                print (e)
                p=p[p['id_product']==int(par)]
                q=None
                refill=None
                p0=None
                for i in p.index:
                    if i>0 and i<max(p.index) and p.at[i,'qnt']==q:
                        p.at[i,'qnt'] = None
                    else:
                        if q!=None and q<p.at[i,'qnt']:
                            #print('<<<',i)
                            refill=i

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

                last_adj = p.iloc[-1]['qnt']-p.iloc[-1]['predicton']
                p=p.append({'date_add':last_dt+pd.DateOffset(days=1),
                                    'index':last_ix+1,'reference':p.iloc[-1]['reference'],'predicton':f(last_ix+1)+last_adj},ignore_index=True)

                for i in range(2,191):
                    if f(last_ix+i)+last_adj>=0:
                        pass
                    else:
                        p=p.append({'date_add':last_dt+pd.DateOffset(days=i),
                                    'index':last_ix+i,'reference':0,'predicton':f(last_ix+i)+last_adj},ignore_index=True)
                        break;

                if i>=190:
                    p=p.append({'date_add':last_dt+pd.DateOffset(days=i),
                                'index':last_ix+i,'predicton':f(last_ix+i),'reference':int(f(last_ix+i)),},ignore_index=True)
                
                if refill:
                    p=p0.append(p,ignore_index=True)
                    #print (p)

            p.to_pickle(store_path)

        return p
