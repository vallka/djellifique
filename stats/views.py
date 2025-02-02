import pandas as pd
import numpy as np

from django.conf import settings
from django.db import connections

from django.views import generic
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

def get_site(request):
    host = request.META['HTTP_HOST']
    if '127.0.0.1' in host or 'gellifique.eu' in host:
        return 'eu'
    else:
        return 'uk'

# Create your views here.
class PageView(LoginRequiredMixin,generic.TemplateView):
    template_name = 'stats/stats.html'

class PageDView(LoginRequiredMixin,generic.TemplateView):
    template_name = 'stats/stats-d.html'
class PageAvgView(LoginRequiredMixin,generic.TemplateView):
    template_name = 'stats/stats-avg.html'

class PageCustView(LoginRequiredMixin,generic.TemplateView):
    template_name = 'stats/stats-cust.html'

class PageCustBhvrView(LoginRequiredMixin,generic.TemplateView):
    template_name = 'stats/stats-cust-bhvr.html'

class PageProductsView(LoginRequiredMixin,generic.TemplateView):
    template_name = 'stats/stats-products.html'

class PageStockView(LoginRequiredMixin,generic.TemplateView):
    template_name = 'stats/stats-stock.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['id_product'] = self.request.GET.get('id_product')
        return context