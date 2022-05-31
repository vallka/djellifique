from django.urls import path

from .views import *

app_name = 'pos'

urlpatterns = [
    path('', PosProductListView.as_view(), name='posproductlist'),
    path('json', PosProductListJson, name='posproductlistjson'),
]

