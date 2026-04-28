from django.urls import path
from .views import article_list_view

app_name = 'main_app'


urlpatterns = [
    path('', article_list_view, name='article_list'),
]