from django.contrib import admin

from gellifihouse.models import *

# Register your models here.
@admin.register(MissGelProducts)
class MissGelProductsAdmin(admin.ModelAdmin):
    list_display = ['id','name', 'color_number', 'packing', 'price', 'gellifique_name', 'gellifique_ean13', 'gellifique_id']
    list_display_links = ['name', 'color_number', 'packing', 'price', ]
    search_fields = ['name', 'color_number', 'packing', 'price', 'gellifique_name', 'gellifique_ean13', 'gellifique_id',
            'gellifique_old_names', 'gellifique_old_ean13', 'gellifique_old_ids']
    list_filter = ['packing', 'price', ]
    list_editable = ['gellifique_name', 'gellifique_ean13', 'gellifique_id',]
    formfield_overrides = {
        models.FloatField: {'widget': admin.widgets.AdminTextInputWidget},
        models.IntegerField: {'widget': admin.widgets.AdminTextInputWidget},
    }
        

class OrderDetailInline(admin.TabularInline):
    model = MissGelOrderDetail
    formfield_overrides = {
        models.FloatField: {'widget': admin.widgets.AdminTextInputWidget},
        models.IntegerField: {'widget': admin.widgets.AdminTextInputWidget},
    }
    extra = 0

@admin.action(description='Allocate to Gellifique UK')
def allocateToGellifiqueUK  (modeladmin, request, queryset):
    for q in queryset:
        q.allocateToShop()

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


@admin.register(MissGelOrderDetail)
class MissGelOrderDetailAdmin(admin.ModelAdmin):
    list_display = ['order', 'product','gellifique_name', 'gellifique_ean13', 'gellifique_id', 'quantity', 'price', 'total_cost']
    list_display_links = ['order', ]
    search_fields = ['order', 'product', 'quantity', 'price', 'total_cost']
    search_fields = ['order', 'name', 'color_number', 'packing', 'price', 'gellifique_name', 'gellifique_ean13', 'gellifique_id',]
    list_filter = ['order', ]

    actions = [allocateToGellifiqueUK]

#admin.site.register(ShopAllocation)
@admin.register(ShopAllocation)
class ShopAllocationAdmin(admin.ModelAdmin):
    pass
    list_display = ['order_name','batch_code', 'shop','order_detail', 'quantity','quantity_left', ]
    list_display_links = list_display
    list_filter = ['order', 'shop', ]
    search_fields = ['gellifique_name','gellifique_ean13',]
    readonly_fields = ['order', 'shop','order_detail','gellifique_name','gellifique_ean13', 'created_dt','updated_dt']


