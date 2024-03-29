from django.contrib import admin
from .models import *

# Register your models here.

@admin.register(Usage)
class UsageAdmin(admin.ModelAdmin):
    list_display = ['created_dt','lang','chars','cached']


@admin.register(GTransCache)
class GTransCacheAdmin(admin.ModelAdmin):
    list_display = ['hash','source']
