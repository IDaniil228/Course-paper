from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect

from .forms import ArticleForm
from .models import Article, Journal
from .filters import ArticleFilter
from django.contrib import messages
from datetime import datetime

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
            title = request.POST.get('title', '').strip()
            if not title:
                form.add_error('title', 'Название статьи обязательно для заполнения')
            # Проверка заполнения научного направления
            scientific_field = request.POST.get('scientific_field', '').strip()
            if not scientific_field:
                form.add_error('scientific_field', 'Научное направление обязательно для заполнения')

            # Проверка заполнения DOI (необязательное поле)
            doi = request.POST.get('doi', '').strip()
            if not doi:
                form.add_error('doi', 'Поле DOI обязательно для заполнения')
            else:
                if not doi.startswith('10.'):
                    form.add_error('doi', 'DOI должен начинаться с "10."')
                elif ' ' in doi:
                    form.add_error('doi', 'DOI не должен содержать пробелов')
                elif len(doi) < 4:
                    form.add_error('doi', 'Слишком короткий DOI')
            # Проверка заполнения года публикации
            publish_year = request.POST.get('publish_year')
            if not publish_year:
                form.add_error('publish_year', 'Год публикации обязателен для заполнения')
            else:
                try:
                    publish_year = int(publish_year)
                    current_year = datetime.now().year
                    if publish_year > current_year:
                        form.add_error('publish_year', f'Год публикации не может быть больше {current_year}г.')
                    elif publish_year < 1900:
                        form.add_error('publish_year', 'Год публикации должен быть не ранее 1900')
                except ValueError:
                    form.add_error('publish_year', 'Год публикации должен быть числом')
            # Привязываем журнал по скрытому ID
            journal_id = form.cleaned_data.get('journal_hidden')
            if journal_id:
                try:
                    article.journal = Journal.objects.get(pk=journal_id)
                except Journal.DoesNotExist:
                    form.add_error('journal_hidden', 'Выбранный журнал не найден')
            else:
                form.add_error('journal_text', 'Необходимо выбрать журнал')

            # Проверка на заполнение поля для автора
            author_ids = request.POST.getlist('authors')
            if not author_ids or all(not author_id for author_id in author_ids):
                form.add_error('authors', 'Необходимо указать хотя бы одного автора')

            # Проверка на заполнение баз цитирования
            db_ids = request.POST.getlist('citation_databases')
            if not db_ids or all(not db_id for db_id in db_ids):
                form.add_error('citation_databases', 'Необходимо выбрать хотя бы одну базу цитирования')

            # Если ошибок не добавилось — сохраняем
            if not form.errors:
                article.save()

                if author_ids:
                    article.authors.set(author_ids)

                if db_ids:
                    article.citation_databases.set(db_ids)

                messages.success(request, 'Статья успешно создана!')
                return redirect('profile')

    else:
        # Предзаполним авторов самим пользователем (можно убрать, если не нужно)
        form = ArticleForm(initial={'authors': [request.user]})
        # Журнал не предзаполняем

    return render(request, 'main_app/create_article.html', {'form': form})