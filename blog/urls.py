from django.urls import path

from .views import *

app_name = 'blog'


urlpatterns = [
    #path('', ListView.as_view(), name='list'),
    #path('home/', HomeView.as_view(), name='home'),
    path('', HomeView.as_view(), name='list'),
    path('search/', SearchView.as_view(), name='search'),
    path('newsletter/<str:slug>/<str:lang>/', NewsletterView.as_view(), name='newsletter'),
    path('newsletter/<str:slug>/', NewsletterView.as_view(), name='newsletter_en'),

    path('makepdf/<str:slug>/<str:lang>/', MakePdfView.as_view(), name='newsletter'),
    path('makepdf/<str:slug>/', MakePdfView.as_view(), name='newsletter_en'),


    #path('category/<str:slug>/', ListView.as_view(), name='post-by-cat'),
    path('category/<str:slug>/', HomeView.as_view(), name='post-by-cat'),

    path('translate/<str:slug>/', translate, name='translate'),  # Default behavior (translates to all predefined languages)
    path('translate/<str:slug>/<str:target_language>/', translate, name='translate_with_language'),

    path('<str:slug>/', PostView.as_view(), name='post'),
]
