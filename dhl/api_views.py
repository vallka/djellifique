from rest_framework import generics
from rest_framework.permissions import IsAuthenticated 
from rest_framework.response import Response
from django.conf import settings

from .models import *
from .views import *

"""
class DHLViewset(viewsets.ModelViewSet):
    #permission_classes = (IsAuthenticated,)     

    # needed here to avoid error
    queryset = DHLParcel.objects.using('presta').raw(DHL_sql())

    serializer_class = DHLSerializer

    def list(self, request, *args, **kwargs):
        # needed here to refresh results, otherwise it is cahced
        self.queryset = DHLParcel.objects.using('presta').raw(DHL_sql())

        # no clone() or all() methods...
        #self.queryset = self.queryset.clone()

        logger.error('DHLViewset list')
        logger.error(self.queryset)

        return super().list(self, request)
"""


class DHLListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)     
    serializer_class = DHLSerializer

    def get(self, request, *args, **kwargs):
        ids = kwargs.get('ids', '')
        ho = kwargs.get('ho', 'o')

        self.queryset = DHLParcel.objects.using('presta').raw(DHL_sql(kwargs.get('ho', 'o'),kwargs.get('ids', '')))

        #logger.info(f'DHLListView:{ho}/{ids}')
        #logger.error(queryset)

        serializer = self.get_serializer(self.queryset, many=True)
    
        return Response(serializer.data)        

