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
class PageAvgView(generic.TemplateView):
    template_name = 'stats/stats-avg.html'

class PageCustView(generic.TemplateView):
    template_name = 'stats/stats-cust.html'

