from django.contrib import admin
from markdownx.admin import MarkdownxModelAdmin
from markdownx.models import MarkdownxField
from django.db import models
from django.forms.widgets import Textarea
from django.utils import timezone

from .models import *

# Register your models here.
#admin.site.register(Post, MarkdownxModelAdmin)
admin.site.register(Category)
class PostLangInline(admin.TabularInline):
    model = PostLang
    fields = ['lang_iso_code','title','email_subject',]
    readonly_fields = ['lang_iso_code','title','email_subject',]
    extra = 0
@admin.register(Post)
class PostAdmin(MarkdownxModelAdmin):
    list_display = ['id','slug','title','blogged','blog_start_dt','newsletter','email_send_dt','created_dt']
    list_display_links = ['id','slug','title',]
    search_fields = ['title', ]
    list_filter = ['blog','email']
    inlines = [PostLangInline]


    def blogged(self,instance):
        return True if instance.blog and instance.blog_start_dt and instance.blog_start_dt<=timezone.now() else False
    
    blogged.boolean = True      
    blogged.short_description = 'Blog'

    def newsletter(self,instance):
        return True if instance.email and instance.email_send_dt and instance.email_send_dt<=timezone.now() else False
    
    newsletter.boolean = True      
    newsletter.short_description = 'News'

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