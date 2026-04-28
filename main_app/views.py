from django.shortcuts import render
from .models import Article
from .filters import ArticleFilter


def article_list_view(request):
    # Получаем все статьи
    queryset = Article.objects.all().select_related('journal').prefetch_related('authors', 'citation_databases')

    # Применяем фильтр из GET-запроса
    f = ArticleFilter(request.GET, queryset=queryset)

    return render(request, 'main_app/article_list.html', {'filter': f})