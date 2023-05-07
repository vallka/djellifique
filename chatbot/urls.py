from django.urls import path

from .views import *

app_name = 'chatbot'

urlpatterns = [
    path('', PageView.as_view(), name='chatbot'),
]
