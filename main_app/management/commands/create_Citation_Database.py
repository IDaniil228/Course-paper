import json
from django.core.management.base import BaseCommand
from main_app.models import CitationDatabase


class Command(BaseCommand):
    help = 'Импорт уникальных баз цитирования из JSONL'

    def add_arguments(self, parser):
        parser.add_argument('jsonl_file', type=str, help='Путь к JSONL файлу')

    def handle(self, *args, **options):
        file_path = options['jsonl_file']
        created_count = 0
        total_lines = 0

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    total_lines += 1
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                        # Извлекаем список баз из текущей строки
                        # Например: ["Scopus", "РИНЦ"]
                        db_list = data.get('citation_databases', [])

                        for db_name in db_list:
                            # Создаем только если такой записи еще нет
                            obj, created = CitationDatabase.objects.get_or_create(name=db_name)
                            if created:
                                created_count += 1
                                self.stdout.write(self.style.SUCCESS(f"Добавлена новая база: {db_name}"))

                    except json.JSONDecodeError:
                        self.stdout.write(self.style.ERROR(f"Ошибка в строке {total_lines}: невалидный JSON"))
                        continue

            self.stdout.write(self.style.SUCCESS(
                f"\nОбработка завершена. Проверено строк: {total_lines}."
                f"\nДобавлено новых уникальных баз в БД: {created_count}"
            ))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Файл {file_path} не найден."))