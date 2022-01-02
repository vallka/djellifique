from django.contrib import admin
from .models import *

# Register your models here.

#admin.site.register(Gellifinsta)
#admin.site.register(Products)
@admin.register(Products)
class ProductsAdmin(admin.ModelAdmin):
    list_display = ['name','is_active']
    search_fields = ['name','is_active', ]

@admin.register(Gellifinsta)
class GellifinstaAdmin(admin.ModelAdmin):
    list_display = ['image_tag','shortcode','taken_at_datetime','is_video','tags_spaced',]
    search_fields = ['shortcode','id']
    #list_filter = ['tags',]
    fields = ['shortcode','taken_at_datetime','created_dt','updated_dt','username','is_active','is_video',
                'file_path','caption','tags','url','image_tag']

    readonly_fields = ['image_tag','created_dt','updated_dt']

    def get_search_results(self, request, queryset, search_term):
        queryset, may_have_duplicates = super().get_search_results(request, queryset, search_term)
        
        #print (queryset.query)

        sql = "SELECT id from `gellifinsta_gellifinsta`"
        sql += " where match(tags) against (%s in boolean mode) limit 0,100"

        queryset2 = self.model.objects.raw(sql,[search_term])

        print( len(queryset2))
        if len(queryset2)>0:
            s=[]
            for row in queryset2:
                s.append(row.id)

            queryset3 = self.model.objects.filter(id__in=s)
            return queryset | queryset3, may_have_duplicates

        return queryset, may_have_duplicates    