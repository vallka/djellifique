from django.contrib import admin
from markdownx.admin import MarkdownxModelAdmin
from markdownx.models import MarkdownxField
from django.db import models
from django.forms.widgets import Textarea

from .models import *

# Register your models here.
#admin.site.register(Post, MarkdownxModelAdmin)
admin.site.register(Category)

@admin.register(Post)
class PostAdmin(MarkdownxModelAdmin):
    list_display = ['id','slug','title','blog','email','created_dt']
    search_fields = ['title', ]

    def get_search_results(self, request, queryset, search_term):
        queryset, may_have_duplicates = super().get_search_results(request, queryset, search_term)
        
        #print (queryset.query)

        sql = "SELECT id from `blog_post`"
        sql += " where match(title,text) against (%s in boolean mode) limit 0,100"

        queryset2 = self.model.objects.raw(sql,[search_term])

        print( len(queryset2))
        if len(queryset2)>0:
            s=[]
            for row in queryset2:
                s.append(row.id)

            queryset3 = self.model.objects.filter(id__in=s)
            return queryset | queryset3, may_have_duplicates

        return queryset, may_have_duplicates    