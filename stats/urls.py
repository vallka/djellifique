from django.urls import path

from .views import *

app_name = 'stats'

urlpatterns = [
    path('', PageView.as_view(), name='stats'),
    path('d', PageDView.as_view(), name='stats-d'),
    path('avg', PageAvgView.as_view(), name='stats-avg'),

    ## ----
    path('df', DfPageView.as_view(), name='dfstats'),
]
