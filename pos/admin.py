from django.contrib import admin

from .models import *

# Register your models here.
#admin.site.register(Product)
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id_product','name','reference','barcode_tag','price','sold','quantity']
    list_display_links = list_display
    search_fields = ['id_product','reference','name','ean13', ]
    readonly_fields = ['barcode_tag','sold']

class DetailInline(admin.TabularInline):
    model = OrderDetail
    extra = 3

    def has_add_permission(self,request, obj):
        return not obj or obj._loaded_values['status']==Order.Status.NEW

    def has_delete_permission(self,request, obj):
        return not obj or obj._loaded_values['status']==Order.Status.NEW

    def has_change_permission(self,request, obj):
        return not obj or obj._loaded_values['status']==Order.Status.NEW

#admin.site.register(Order)
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [DetailInline]
    list_display = ['id','customer_name','customer_email','total','status',]
    list_display_links = list_display
    search_fields = ['id','customer_name','customer_email','total' ]
    list_filter = ['status']
