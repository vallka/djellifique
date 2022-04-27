from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated 

from .models import *
from .views import *

import logging
logger = logging.getLogger(__name__)

class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)     
    queryset = MissGelProducts.objects.all()
    serializer_class = MissGelProductSerializer

