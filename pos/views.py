from django.shortcuts import render
from django.views import generic
from django.http import JsonResponse

from .models import *

# Create your views here.
class PosProductListView(generic.ListView):
    model = Product


def PosProductListJson(request):
    products = list(Product.objects.values())
    return JsonResponse(products,safe=False)
