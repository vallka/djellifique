from django.contrib import admin

from gellifihouse.models import *

# Register your models here.
@admin.register(MissGelProducts)
class MissGelProductsAdmin(admin.ModelAdmin):
    list_display = ['id','name', 'color_number', 'packing', 'price', 'gellifique_name', 'gellifique_ean13', 'gellifique_id']
    list_display_links = ['name', 'color_number', 'packing', 'price', 'gellifique_name', 'gellifique_ean13', ]
    search_fields = ['name', 'color_number', 'packing', 'price', 'gellifique_name', 'gellifique_ean13', 'gellifique_id',
            'gellifique_old_names', 'gellifique_old_ean13', 'gellifique_old_ids']
    list_filter = ['packing', 'price', ]
        

class OrderDetailInline(admin.TabularInline):
    model = MissGelOrderDetail
    formfield_overrides = {
        models.FloatField: {'widget': admin.widgets.AdminTextInputWidget},
        models.IntegerField: {'widget': admin.widgets.AdminTextInputWidget},
    }
    extra = 0

@admin.register(MissGelOrders)
class MissGelOrdersAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'status', 'order_dt', 'received_dt', 'batch_code', 'gellifique_code', 'total_cost']
    list_display_links = ['name', 'status', 'order_dt', 'received_dt', ]
    search_fields = ['name', 'status', ]
    list_filter = ['status', 'order_dt', 'received_dt', ]
    formfield_overrides = {
        models.FloatField: {'widget': admin.widgets.AdminTextInputWidget},
    }
    inlines = [OrderDetailInline]


#@admin.register(MissGelOrderDetail)
#class MissGelOrderDetailAdmin(admin.ModelAdmin):
#    list_display = ['order', 'product','name', 'color_number', 'packing', 'quantity', 'price', 'total_cost']
#    list_display_links = ['order', ]
#    search_fields = ['order', 'product', 'quantity', 'price', 'total_cost']
#    list_filter = ['order', ]
#    list_editable = ['product','quantity', 'price', 'total_cost']

