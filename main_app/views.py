from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect

from .forms import ArticleForm
from .models import Article, Journal
from .filters import ArticleFilter
from django.contrib import messages


def article_list_view(request):
    # Получаем все статьи
    queryset = Article.objects.all().select_related('journal').prefetch_related('authors', 'citation_databases')

    # Применяем фильтр из GET-запроса
    f = ArticleFilter(request.GET, queryset=queryset)

    return render(request, 'main_app/article_list.html', {'filter': f})


def user_login(request):
    """Авторизация пользователя (только вход, без регистрации)"""
    # Если пользователь уже вошёл, сразу на профиль
    if request.user.is_authenticated:
        return redirect('profile')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        print(username)
        print(password)

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.get_full_name() or user.username}!')
            return redirect('profile')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')

    return render(request, 'main_app/login.html')


def user_logout(request):
    """Выход из системы"""
    logout(request)
    return redirect('login')


@login_required
def profile(request):
    """Профиль авторизованного автора: имя и список его статей"""
    author = request.user  # это экземпляр Author
    articles = author.articles.all().order_by('-publish_year', 'title')  # связь через related_name='articles'

    context = {
        'author': author,
        'articles': articles,
    }
    return render(request, 'main_app/profile.html', context)

def search_journal(request):
    """Эндпоинт для автодополнения журналов (JSON)"""
    term = request.GET.get('term', '').strip()
    if len(term) < 2:
        return JsonResponse([], safe=False)

    journals = Journal.objects.filter(title__icontains=term)[:15]
    results = [{'id': j.id, 'text': j.title} for j in journals]
    return JsonResponse(results, safe=False)


@login_required
def create_article(request):
    """Страница создания новой статьи"""
    if request.method == 'POST':
        print("POST данные:", request.POST)
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)

            # Привязываем журнал по скрытому ID
            journal_id = form.cleaned_data.get('journal_hidden')
            if journal_id:
                try:
                    article.journal = Journal.objects.get(pk=journal_id)
                except Journal.DoesNotExist:
                    form.add_error('journal_hidden', 'Выбранный журнал не найден')
            else:
                form.add_error('journal_text', 'Необходимо выбрать журнал')

            # Если ошибок не добавилось — сохраняем
            if not form.errors:
                article.save()

                author_ids = request.POST.getlist('authors')  # ['94']
                if author_ids:
                    article.authors.set(author_ids)

                # Аналогично для баз цитирования
                db_ids = request.POST.getlist('citation_databases')
                if db_ids:
                    article.citation_databases.set(db_ids)

                messages.success(request, 'Статья успешно создана!')
                return redirect('profile')

    else:
        # Предзаполним авторов самим пользователем (можно убрать, если не нужно)
        form = ArticleForm(initial={'authors': [request.user]})
        # Журнал не предзаполняем
    print(1)
    return render(request, 'main_app/create_article.html', {'form': form})