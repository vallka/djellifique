# Create your views here.
from django.shortcuts import render
from django.views import generic
from rest_framework import serializers

import logging
logger = logging.getLogger(__name__)

from .models import *

# Create your views here.
class IndexView(generic.ListView):

    def get_queryset(self):
        """
        """
        qs = DHLParcel.objects.using('presta').raw(DHL_sql('o',''))
        logger.info('get_queryset')
        logger.error(qs)
        return qs

class DHLSerializer(serializers.ModelSerializer):
    class Meta:
        model = DHLParcel
        fields = '__all__'

