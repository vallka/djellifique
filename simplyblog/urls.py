"""simplyblog URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import include, path, re_path
from django.conf import settings

from django.conf.urls.static import static 
from django.shortcuts import redirect

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from ups.api_views import *
from prestashop.api_views import *
from stats.api_views import *


schema_view = get_schema_view(
   openapi.Info(
      title="PyRestaShop API",
      default_version='v1',
      description="PyRestaShop API description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@vallka.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('', lambda request: redirect('blog/')),
    path('blog/admin/', admin.site.urls),
    path('blog/newsletter/', include('newsletter.urls')),
    path('blog/', include('blog.urls')),
    path('prestashop/', include('prestashop.urls')),
    path('stats/', include('stats.urls')),
    path('admin/', admin.site.urls),
    path('markdownx/', include('markdownx.urls')),

    path('api/v1/ups/action/', UPSAction.as_view()),
    path('api/v1/ups/list/<str:ids>/', UPSListView.as_view()),
    path('api/v1/ups/label/', UPSLabelAction.as_view()),

    path('api/v1/prestashop/product/update/', UpdateProduct.as_view()),
    path('api/v1/prestashop/product/<str:ids>/', ProductList.as_view()),
    path('api/v1/prestashop/order/', OrderList.as_view()),
    path('api/v1/prestashop/order/<int:id_order>/', OrderDetailList.as_view()),
    path('api/v1/prestashop/order/updatestatus/', UpdateOrderStatus.as_view()),

    path('api/v1/stats/monthlysalestable/<str:par>/', SalesTableView.as_view()),
    path('api/v1/stats/monthlysalesfig/<str:par>/', SalesFigView.as_view()),

    # ---
    path('api/v1/stats/dailysales/', DailySalesView.as_view()),
    path('api/v1/stats/monthlysales/', MonthlySalesView.as_view()),
    path('api/v1/stats/yearlysales/', YearlySalesView.as_view()),
    # ---

    re_path(r'^api/v1/swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('api/v1/swagger/<slug:format>', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('api/v1/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/v1/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
] + urlpatterns

