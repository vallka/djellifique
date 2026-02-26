from django.urls import path

from .views import *

app_name = "prestashop"

urlpatterns = [
    path("product/", ProductListView.as_view(), name="product"),
    path("productinfo/", ProductInfoView.as_view(), name="productinfo"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("order/", OrderListView.as_view(), name="order"),
    path("order/<int:id_order>/", OrderDetailListView.as_view(), name="order_detail"),
    path("upload-cert/<str:email>/put.method/", putfile, name="putmethod"),
    path("upload-cert/<str:email>/", UploadPageView.as_view(), name="upload-cert"),
    path("customer-cert/<str:email>/", CertListView.as_view(), name="cert-list"),
    path("customer-cert-json/<str:email>/", CertListJsonView.as_view(), name="cert-json"),
    path("printcategory/<int:id_category>/", PrintCategoryView.as_view(), name="printcategory"),
    path("printcategories/", PrintCategoriesView.as_view(), name="printcategories"),
    path("printcolours/<int:id_category>/", PrintColoursView.as_view(), name="printcolours"),
    path("colourchart/", ColourChartView.as_view(), name="colourchart_default"),
    path("colourchart/<int:id_category>/", ColourChartView.as_view(), name="colourchart"),
    path("save_sort/", save_sort, name="save_sort"),
]
