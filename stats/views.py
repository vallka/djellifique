import pandas as pd
import numpy as np

from django.conf import settings
from django.db import connections

from django.views import generic
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin


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
