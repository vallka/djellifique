from django.urls import path

from .views import *

app_name = 'stats'

urlpatterns = [
    path('', PageView.as_view(), name='stats'),
    path('d', PageDView.as_view(), name='stats-d'),
    path('avg', PageAvgView.as_view(), name='stats-avg'),

    path('customers', PageCustView.as_view(), name='stats-cust'),
    path('customers-behaviour', PageCustBhvrView.as_view(), name='stats-cust-bhvr'),

    path('products', PageProductsView.as_view(), name='stats-products'),

    

]
