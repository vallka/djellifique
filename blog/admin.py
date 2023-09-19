from django.contrib import admin
from markdownx.admin import MarkdownxModelAdmin
from markdownx.models import MarkdownxField
from django.db import models
from django.forms.widgets import Textarea
from django import forms
from django.utils import timezone
from django.urls import reverse
from django.utils.html import format_html

from .models import *

# Register your models here.
#admin.site.register(Post, MarkdownxModelAdmin)
admin.site.register(Category)
admin.site.register(CategoryLang)
@admin.register(PostLang)
class PostLangAdmin(MarkdownxModelAdmin):
    list_display = ['post','slug','lang_iso_code','title','email_subject',]
    list_display_links = ['post','title','email_subject',]
    #list_filter = ['post']
    readonly_fields = ['slug']


class PostLangInline(admin.TabularInline):
    model = PostLang
    fields = ['lang_iso_code','title','email_subject','edit_link']
    readonly_fields = ['lang_iso_code','title','email_subject','edit_link',]
    extra = 0
    
    def edit_link(self, obj):
        url = reverse('admin:blog_postlang_change', args=[obj.pk])
        return format_html('<a href="{}" target="_blank">Edit</a>', url)

    edit_link.short_description = 'Edit'


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Check if the instance has a primary key, indicating it's an existing object
        if self.instance and self.instance.pk:
            if '-copy' in self.instance.slug:
                self.initial['slug'] = ''

    def clean(self):
        cleaned_data = super().clean()
        print('postform clear')
        # Check if "Save as new" is being performed
        if self.data.get("_saveasnew"):
            print('postform clear as new')
            # Modify the field causing the unique constraint error
            # For example, if it's a 'slug' field:
            cleaned_data['slug'] = ''
            cleaned_data['title'] += " (copy)"
            cleaned_data['slug'] = ''
            cleaned_data['blog'] = False
            cleaned_data['blog_start_dt'] = None
            cleaned_data['email'] = False
            cleaned_data['email_send_dt'] = None
            cleaned_data['email_status'] = Post.EmailStatus.NONE

        return cleaned_data

@admin.register(Post)
class PostAdmin(MarkdownxModelAdmin):
    list_display = ['id','slug','title','email_subject','domain','blogged','f_blog_start_dt','newsletter','f_email_send_dt','formatted_created_dt']
    list_display_links = ['id','slug','title','email_subject',]
    search_fields = ['title', ]
    list_filter = ['blog','email','domain']
    inlines = [PostLangInline]
    save_as = True
    form = PostForm

    def formatted_created_dt(self, obj):
        return obj.created_dt.strftime("%d-%m-%Y %H:%M")
    formatted_created_dt.admin_order_field = 'created_dt'
    formatted_created_dt.short_description = 'Created dt'

    def f_blog_start_dt(self, obj):
        return obj.blog_start_dt.strftime("%d-%m-%Y %H:%M") if obj.blog_start_dt else ""
    f_blog_start_dt.admin_order_field = 'blog_start_dt'
    f_blog_start_dt.short_description = 'Published'

    def f_email_send_dt(self, obj):
        return obj.email_send_dt.strftime("%d-%m-%Y %H:%M") if obj.email_send_dt else ""
    f_email_send_dt.admin_order_field = 'email_send_dt'
    f_email_send_dt.short_description = 'Sent'

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
    
