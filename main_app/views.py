from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect

from .forms import ArticleForm, AuthorForm
from .models import Article, Journal, CoAuthor
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
    if request.method == 'POST':
        form = ArticleForm(request.POST)

        # 1. Получаем списки внешних соавторов сразу (они нам нужны для сохранения)
        co_names = request.POST.getlist('co_full_name[]')
        co_statuses = request.POST.getlist('co_status[]')
        co_orgs = request.POST.getlist('co_organization[]')

        # 2. Вызываем is_valid(), чтобы Django заполнил form.errors стандартными ошибками
        is_django_valid = form.is_valid()

        # 3. РУЧНЫЕ ПРОВЕРКИ (теперь они выполняются ВСЕГДА)

        # Название
        title = request.POST.get('title', '').strip()
        if not title:
            form.add_error('title', 'Название статьи обязательно для заполнения')

        # Научное направление
        scientific_field = request.POST.get('scientific_field', '').strip()
        if not scientific_field:
            form.add_error('scientific_field', 'Научное направление обязательно для заполнения')

        # DOI
        doi = request.POST.get('doi', '').strip()
        if not doi:
            form.add_error('doi', 'Поле DOI обязательно для заполнения')
        else:
            if not doi.startswith('10.'):
                form.add_error('doi', 'DOI должен начинаться с "10."')
            elif ' ' in doi:
                form.add_error('doi', 'DOI не должен содержать пробелов')

        # Год
        publish_year = request.POST.get('publish_year')
        if not publish_year:
            form.add_error('publish_year', 'Год публикации обязателен для заполнения')
        else:
            try:
                py = int(publish_year)
                current_year = datetime.now().year
                if py > current_year:
                    form.add_error('publish_year', f'Год не может быть больше {current_year}')
                elif py < 1900:
                    form.add_error('publish_year', 'Год должен быть не ранее 1900')
            except ValueError:
                form.add_error('publish_year', 'Год должен быть числом')

        # Журнал
        journal_id = request.POST.get('journal_hidden')
        if not journal_id:
            form.add_error('journal_text', 'Необходимо выбрать журнал из списка')

        # Базы цитирования
        db_ids = request.POST.getlist('citation_databases')
        if not db_ids:
            form.add_error('citation_databases', 'Выберите хотя бы одну базу')

        # Авторы (Внутренние + Внешние)
        author_ids = request.POST.getlist('authors')
        # Считаем, что автор есть, если выбран либо системный автор, либо добавлен хотя бы один внешний
        has_external = any(name.strip() for name in co_names)
        if not author_ids and not has_external:
            form.add_error('authors', 'Необходимо указать хотя бы одного автора (системного или внешнего)')
            # 4. ИТОГОВАЯ ПРОВЕРКА: если Django-форма ок И наших ручных ошибок нет

        print("--- ОШИБКИ В КОНСОЛИ ---")
        print(form.errors)
        print("------------------------")
        if is_django_valid and not form.errors:
            article = form.save(commit=False)

            # Привязываем журнал
            try:
                article.journal = Journal.objects.get(pk=journal_id)
            except:
                form.add_error('journal_text', 'Ошибка привязки журнала')
                return render(request, 'main_app/create_article.html', {'form': form})

            article.save()  # Сохраняем статью

            # Сохраняем Many-to-Many поля
            if author_ids:
                article.authors.set(author_ids)
            if db_ids:
                article.citation_databases.set(db_ids)

            # Сохраняем внешних соавторов
            for i in range(len(co_names)):
                if co_names[i].strip():
                    current_org = None
                    if i < len(co_orgs):
                        current_org = co_orgs[i] if co_statuses[i] == 'external' else None

                    CoAuthor.objects.create(
                        article=article,
                        full_name=co_names[i],
                        status=co_statuses[i],
                        organization=current_org
                    )

            messages.success(request, 'Статья успешно создана!')
            return redirect('profile')

    else:
        form = ArticleForm(initial={'authors': [request.user]})

    return render(request, 'main_app/create_article.html', {'form': form})


def add_author_view(request):
    if request.method == 'POST':
        form = AuthorForm(request.POST)
        if form.is_valid():
            # Создаем объект автора, но не сохраняем в базу сразу
            author = form.save(commit=False)

            # ВАЖНО: Хэшируем пароль (чтобы он не лежал в базе открытым текстом)
            password = form.cleaned_data['password']
            author.set_password(password)

            # Теперь сохраняем окончательно
            author.save()

            messages.success(request, f'Автор {author.get_full_name()} успешно добавлен!')
            return redirect('profile')  # Перенаправляем на ту же страницу или на список
    else:
        form = AuthorForm()

    return render(request, 'main_app/create_author.html', {'form': form})