import json
import re
import requests
import random
import csv
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from main_app.models import Article, Author, Journal, CitationDatabase


class Command(BaseCommand):
    help = 'Импорт статей с логированием прогресса и обращений к API'

    def add_arguments(self, parser):
        parser.add_argument('jsonl_file', type=str, help='Путь к JSONL файлу')
        parser.add_argument('--csv_output', type=str, default='skipped_journals.csv')

    def get_issns_from_crossref(self, doi):
        if not doi: return []
        url = f"https://api.crossref.org/works/{doi}"
        try:
            # Выводим сообщение о запросе, чтобы пользователь видел активность
            self.stdout.write(f"  --> Запрос Crossref API для DOI: {doi}...", ending='')
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS(" [OK]"))
                return response.json().get('message', {}).get('ISSN', [])
            else:
                self.stdout.write(self.style.WARNING(f" [Код {response.status_code}]"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f" [Ошибка API: {e}]"))
        return []

    def parse_initials(self, name_str):
        parts = re.sub(r'\.', ' ', name_str).split()
        l_name = parts[0] if len(parts) > 0 else ""
        f_init = parts[1][0] if len(parts) > 1 else ""
        p_init = parts[2][0] if len(parts) > 2 else ""
        return l_name, f_init, p_init

    def handle(self, *args, **options):
        file_path = options['jsonl_file']
        csv_file_path = options['csv_output']

        stats = {'total': 0, 'created': 0, 'already_exists': 0, 'skipped_no_journal': 0, 'errors': 0}

        # Кэш журналов, чтобы не запрашивать базу по 100 раз для одного и того же издания
        journal_cache = {}

        try:
            with open(csv_file_path, mode='w', encoding='utf-8-sig', newline='') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=['doi', 'journal_name_json', 'article_title'],
                                        delimiter=';')
                writer.writeheader()

                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        stats['total'] += 1
                        line = line.strip()
                        if not line: continue

                        # Вывод прогресса каждые 10 строк
                        if stats['total'] % 10 == 0:
                            self.stdout.write(f"Обработано строк: {stats['total']}...")

                        try:
                            data = json.loads(line)
                        except json.JSONDecodeError:
                            stats['errors'] += 1
                            continue

                        art_info = data.get('article', {})
                        doi = art_info.get('doi', '').strip()
                        journal_name = data.get('journal_name', '').strip()
                        title = art_info.get('title') or "Без названия"

                        # 1. Быстрая проверка на дубликат
                        if doi and Article.objects.filter(doi=doi).exists():
                            stats['already_exists'] += 1
                            continue

                        # 2. Поиск журнала (сначала в кэше)
                        journal = journal_cache.get(journal_name)

                        if not journal:
                            # Пробуем через API, если есть DOI
                            if doi:
                                crossref_issns = self.get_issns_from_crossref(doi)
                                for issn in crossref_issns:
                                    journal = Journal.objects.filter(issns__icontains=issn).first()
                                    if journal: break

                            # Если не нашли по ISSN, ищем по названию
                            if not journal:
                                journal = Journal.objects.filter(title__iexact=journal_name).first()

                            # Если нашли — сохраняем в кэш
                            if journal:
                                journal_cache[journal_name] = journal

                        # Если журнал так и не найден
                        if not journal:
                            writer.writerow(
                                {'doi': doi or "НЕТ DOI", 'journal_name_json': journal_name, 'article_title': title})
                            stats['skipped_no_journal'] += 1
                            continue

                        # 3. Сохранение данных
                        try:
                            with transaction.atomic():
                                foreign_map = {'yes': True, 'no': False}
                                article = Article.objects.create(
                                    title=title,
                                    publish_year=art_info.get('publish_year'),
                                    full_biblio_description=art_info.get('full_biblio_description'),
                                    doi=doi or None,
                                    scientific_field=art_info.get('scientific_field'),
                                    total_authors_count=art_info.get('total_authors_count'),
                                    with_foreign_authors=foreign_map.get(art_info.get('with_foreign_authors')),
                                    journal=journal,
                                )

                                for db_name in data.get('citation_databases', []):
                                    db_obj, _ = CitationDatabase.objects.get_or_create(name=db_name)
                                    article.citation_databases.add(db_obj)

                                for auth_data in data.get('authors', []):
                                    raw_name = auth_data.get('full_name')
                                    l_name, f_init, p_init = self.parse_initials(raw_name)
                                    author_obj = Author.objects.filter(last_name__iexact=l_name,
                                                                       first_name__istartswith=f_init,
                                                                       patronymic__istartswith=p_init).first()

                                    if not author_obj:
                                        username = f"{slugify(l_name, allow_unicode=True)}_{f_init.lower()}_{random.randint(1000, 9999)}"
                                        author_obj = Author.objects.create(username=username, last_name=l_name,
                                                                           first_name=f_init + ".",
                                                                           patronymic=p_init + "." if p_init else "")
                                        author_obj.set_unusable_password()
                                        author_obj.save()
                                    article.authors.add(author_obj)
                                stats['created'] += 1
                                self.stdout.write(self.style.SUCCESS(f"  + Статья добавлена: {title[:40]}..."))

                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"  ! Ошибка сохранения: {e}"))
                            stats['errors'] += 1

            self.stdout.write("\n" + "=" * 50)
            self.stdout.write(self.style.SUCCESS(
                f"ГОТОВО. Новых статей: {stats['created']}, Пропущено: {stats['skipped_no_journal']}"))
            self.stdout.write(f"Отчет о пропусках: {csv_file_path}")

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Файл {file_path} не найден."))