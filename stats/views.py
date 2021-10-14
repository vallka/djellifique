from django.views import generic
from django.shortcuts import render

# Create your views here.
class PageView(generic.TemplateView):
    template_name = 'stats/stats.html'
