from django.urls import path
from . import views

urlpatterns = [
    path('', views.article_list_view, name='article_list'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('article/create/', views.create_article, name='create_article'),
    path('api/journal-search/', views.search_journal, name='journal_search'),
]