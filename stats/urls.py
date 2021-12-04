from django.urls import path

from .views import *

app_name = 'stats'

urlpatterns = [
    path('', PageView.as_view(), name='stats'),
    path('df', DfPageView.as_view(), name='dfstats'),
]
