from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path

# Register your models here.

class CustomAdminSite(admin.AdminSite):
  
    def get_urls(self):
        urls = super(CustomAdminSite, self).get_urls()
        my_urls = [
            path('my_view/', self.my_view),
        ]
        return my_urls + urls

        custom_urls = [
            url(r'desired/path$', self.admin_view(organization_admin.preview), name="preview"),
        ]
        return urls + custom_urls


    def my_view(self, request):
        return TemplateResponse(request, "stats/stats.html", )