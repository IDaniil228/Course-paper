from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect

from .forms import ArticleForm, AuthorForm
from .models import Article, Journal, CoAuthor
from .filters import ArticleFilter
from django.contrib import messages
from datetime import datetime
import openpyxl
from django.http import HttpResponse
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from .models import Article, CitationDatabase  # Импортируй модель баз!


def article_list_view(request):
    queryset = Article.objects.all()
    f = ArticleFilter(request.GET, queryset=queryset)

    # ОБЯЗАТЕЛЬНО: получаем базы, чтобы они отобразились в модальном окне
    all_databases = CitationDatabase.objects.all()

    return render(request, 'main_app/article_list.html', {
        'filter': f,
        'all_databases': all_databases  # Передаем в шаблон
    })
def export_articles_excel(request):
    # 1. Получаем данные из параметров модального окна
    year = request.GET.get('year')
    db_id = request.GET.get('database')
    level = request.GET.get('level')

    # 2. Базовый запрос с оптимизацией (select_related и prefetch_related)
    articles_qs = Article.objects.all().select_related('journal').prefetch_related(
        'authors', 'citation_databases', 'coauthors'
    )

    # 3. Фильтрация
    if year and year.strip():
        articles_qs = articles_qs.filter(publish_year=year)
    if db_id and db_id.strip():
        articles_qs = articles_qs.filter(citation_databases__id=db_id)
    if level and level.strip():
        articles_qs = articles_qs.filter(journal__level=level)

    # 4. Создаем Excel книгу
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Научный отчет"

    # --- ОПРЕДЕЛЯЕМ СТИЛИ (как на скриншоте) ---
    thin_side = Side(style='thin')
    border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

    header_fill = PatternFill(start_color="D9EAD3", end_color="D9EAD3", fill_type="solid")  # Салатовый
    number_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")  # Светло-салатовый

    header_font = Font(bold=True, size=10)
    base_alignment = Alignment(vertical='top', wrap_text=True, horizontal='left')
    center_alignment = Alignment(vertical='top', wrap_text=True, horizontal='center')

    # 5. ШАПКА ТАБЛИЦЫ (Названия колонок)
    headers = [
        "Статья (полное библиографическое описание)",  # 1
        "Авторский перевод названия",  # 2
        "База цитирования",  # 3
        "Идентификатор DOI",  # 4
        "Наименование издания (журнала)",  # 5
        "Направление (область науки)",  # 6
        "Приоритетное направление КФУ",  # 7
        "Авторы сотрудники",  # 8
        "из них (статус)",  # 9
        "Другие авторы (внешние/студенты)",  # 10
        "Наименование организации"  # 11
    ]
    ws.append(headers)

    # 6. ВТОРАЯ СТРОКА (Нумерация колонок 1, 2, 3...)
    ws.append([i for i in range(1, len(headers) + 1)])

    # Применяем стили к шапке
    for row_idx in [1, 2]:
        for cell in ws[row_idx]:
            cell.font = header_font
            cell.border = border
            cell.alignment = center_alignment
            cell.fill = header_fill if row_idx == 1 else number_fill

    # 7. ЗАПОЛНЕНИЕ ДАННЫМИ
    for article in articles_qs:
        # Сбор внутренних авторов
        internal_authors = "\n".join([f"{a.last_name} {a.first_name}" for a in article.authors.all()])

        # Сбор баз цитирования
        dbs = ", ".join([db.name for db in article.citation_databases.all()])

        # Сбор внешних авторов и организаций (модель CoAuthor)
        ext_list = article.coauthors.all()
        external_names = "\n".join([ca.full_name for ca in ext_list])
        external_orgs = "\n".join(list(set([ca.organization for ca in ext_list if ca.organization])))

        # Сбор статусов (пример логики)
        statuses = "\n".join(["сотрудник" for _ in article.authors.all()])

        # Формируем библиографическую строку
        biblio = article.full_biblio_description
        if not biblio:
            j_title = article.journal.title if article.journal else "—"
            biblio = f"{article.title} // {j_title}. — {article.publish_year}."

        row_data = [
            biblio,  # 1
            "—",  # 2 (заглушка)
            dbs,  # 3
            article.doi or "—",  # 4
            article.journal.title if article.journal else "—",  # 5
            article.scientific_field or "—",  # 6
            "—",  # 7 (заглушка)
            internal_authors,  # 8
            statuses,  # 9
            external_names,  # 10
            external_orgs  # 11
        ]
        ws.append(row_data)

        # Применяем стили к ячейкам текущей строки
        for cell in ws[ws.max_row]:
            cell.border = border
            cell.alignment = base_alignment

    # 8. НАСТРОЙКА ШИРИНЫ КОЛОНОК (чтобы было красиво)
    widths = [50, 25, 15, 25, 30, 25, 20, 25, 15, 25, 30]
    for i, width in enumerate(widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width

    # 9. ФИКСАЦИЯ ШАПКИ
    ws.freeze_panes = "A3"

    # 10. ФОРМИРОВАНИЕ ОТВЕТА
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    response['Content-Disposition'] = f'attachment; filename="Scientific_Report_{timestamp}.xlsx"'

    wb.save(response)
    return response
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