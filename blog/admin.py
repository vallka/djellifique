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
    list_display = ['id','title','email_subject','domain','draft','f_page','f_blog','f_blog_start_dt','f_news','f_email_send_dt','f_planned_dt']
    list_display_links = ['id','title','email_subject',]
    search_fields = ['title', ]
    list_filter = ['draft','page','blog','email','email_status','domain']
    date_hierarchy = 'planned_dt'
    inlines = [PostLangInline]
    save_as = True
    form = PostForm

    def f_created_dt(self, obj):
        return obj.created_dt.strftime("%d/%m/%y %H:%M")
    f_created_dt.admin_order_field = 'created_dt'
    f_created_dt.short_description = 'Created dt'

    def f_planned_dt(self, obj):
        return obj.planned_dt.strftime("%d/%m/%y") if obj.planned_dt else None
    f_planned_dt.admin_order_field = 'planned_dt'
    f_planned_dt.short_description = 'Planned dt'

    def f_blog_start_dt(self, obj):
        return obj.blog_start_dt.strftime("%d/%m/%y %H:%M") if obj.blog_start_dt else ""
    f_blog_start_dt.admin_order_field = 'blog_start_dt'
    f_blog_start_dt.short_description = 'Published'

    def f_email_send_dt(self, obj):
        return obj.email_send_dt.strftime("%d/%m/%y %H:%M") if obj.email_send_dt else ""
    f_email_send_dt.admin_order_field = 'email_send_dt'
    f_email_send_dt.short_description = 'Sent'

    def f_page(self,obj):
        return obj.page
    f_page.admin_order_field = 'page'
    f_page.short_description = 'Page'
    f_page.boolean = True      

    def f_blog(self,obj):
        return obj.blog
    f_blog.admin_order_field = 'blog'
    f_blog.short_description = 'Blog'
    f_blog.boolean = True      

    def f_news(self,obj):
        return obj.email
    f_news.admin_order_field = 'email'
    f_news.short_description = 'News'
    f_news.boolean = True      

    def blogged(self,instance):
        return True if instance.blog and instance.blog_start_dt and instance.blog_start_dt<=timezone.now() else False
    blogged.boolean = True      
    blogged.short_description = 'Blog'

    def newsletter(self,instance):
        return True if instance.email and instance.email_send_dt and instance.email_send_dt<=timezone.now() else False
    newsletter.boolean = True      
    newsletter.short_description = 'News'

    def get_search_results(self, request, queryset, search_term):
        queryset, may_have_duplicates = super().get_search_results(request, queryset, '')
        
        if not search_term:
            return queryset, may_have_duplicates

        #print (queryset.query)

        sql = "SELECT id from `blog_post`"
        sql += " where match(title,text) against (%s in boolean mode) limit 0,100"

        queryset2 = self.model.objects.raw(sql,[search_term])

        queryset3 = queryset.filter(id__in=[o.id for o in queryset2])

        print( len(queryset),len(queryset2),len(queryset3))
        return queryset3, may_have_duplicates

    
