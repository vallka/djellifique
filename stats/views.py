import pandas as pd
import numpy as np

from django.conf import settings
from django.db import connections

from django.views import generic
from django.shortcuts import render

# Create your views here.
class PageView(generic.TemplateView):
    template_name = 'stats/stats.html'

class PageDView(generic.TemplateView):
    template_name = 'stats/stats-d.html'
class PageDWView(generic.TemplateView):
    template_name = 'stats/stats-dw.html'


## ----


class DfPageView(generic.TemplateView):
    template_name = 'stats/statsdf.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        daily = self.get_data()

        daily['GBP_shipping'] = daily['GBP_shipping'].astype(float)
        daily['GBP_products'] = daily['GBP_products'].astype(float)
        daily['GBP_cost'] = daily['GBP_cost'].astype(float)

        daily['VAT 8pc'] = round(daily['GBP_products']*0.08,2)
        daily['Gross Margin'] = daily['GBP_products'] - daily['VAT 8pc'] - daily['GBP_cost']


        annually = daily.groupby(['Y',]).agg({'products':np.sum,
                                            'products_discounted':np.sum,
                                            'orders':np.sum,
                                            'GBP_cost':np.sum,
                                            'GBP_products':np.sum,
                                            'GBP_shipping':np.sum,
                                            'GBP_paid':np.sum,
                                            'VAT 8pc':np.sum,
                                            'Gross Margin':np.sum,
                                            }).sort_index(ascending=False)

        monthly = daily.groupby(['Y','M']).agg({'products':np.sum,
                                            'products_discounted':np.sum,
                                            'orders':np.sum,
                                            'GBP_cost':np.sum,
                                            'GBP_products':np.sum,
                                            'GBP_shipping':np.sum,
                                            'GBP_paid':np.sum,
                                            'VAT 8pc':np.sum,
                                            'Gross Margin':np.sum,
                                            }).sort_index(ascending=False)

        qly = daily.groupby(['Y','Q']).agg({'products':np.sum,
                                            'products_discounted':np.sum,
                                            'orders':np.sum,
                                            'GBP_cost':np.sum,
                                            'GBP_products':np.sum,
                                            'GBP_shipping':np.sum,
                                            'GBP_paid':np.sum,
                                            'VAT 8pc':np.sum,
                                            'Gross Margin':np.sum,
                                            }).sort_index(ascending=False)

        context['data'] = annually.to_html()

        return context        

    @staticmethod
    def get_sql():
        return '''
SELECT
YEAR(DATE_ADD) Y,
QUARTER(DATE_ADD) q,
MONTH(DATE_ADD) m,
DAY(DATE_ADD) d,
SUM((SELECT SUM(product_quantity) FROM ps17_order_detail d WHERE id_order=o.id_order)) products,
SUM((SELECT SUM(product_quantity) FROM ps17_order_detail d WHERE id_order=o.id_order AND reduction_percent>0)) products_discounted,
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
        '''

    @staticmethod
    def get_cols():
        return ['Y','Q','M','D','products','products_discounted','orders','GBP_cost','GBP_products','GBP_shipping','GBP_paid']

    @staticmethod
    def get_data():
        with connections['presta'].cursor() as cursor:
            cursor.execute(DfPageView.get_sql(),)
            rows = cursor.fetchall()

        return pd.DataFrame(rows, columns=DfPageView.get_cols())