from rest_framework import serializers
from .models import *

# Create your views here.
class MissGelProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = MissGelProducts
        fields = '__all__'
