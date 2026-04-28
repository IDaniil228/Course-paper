from django.core.management.base import BaseCommand
import json

from main_app.models import Journal, Author  # ЗАМЕНИТЕ your_app на ваше приложение


class Command(BaseCommand):
    help = 'Импорт данных: авторы из json'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Путь к файлу CSV')

    def handle(self, *args, **options):
        try:
            with open(options['json_file'], 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка чтения: {e}"))
            return

        for item in data:
            try:
                # 1. Разбираем ФИО (Предполагаем формат: Фамилия Имя Отчество)
                full_name = item.get('full_name', '')
                name_parts = full_name.split()

                last_name = name_parts[0] if len(name_parts) > 0 else ''
                first_name = name_parts[1] if len(name_parts) > 1 else ''
                patronymic = name_parts[2] if len(name_parts) > 2 else ''

                # 2. Генерируем username (используем Scopus ID или ORCID)
                # Если их нет, используем фамилию (но это может быть не уникально)
                username = item.get('scopus_id') or item.get('orcid')

                if not username:
                    self.stdout.write(self.style.WARNING(f"Пропуск {full_name}: нет ID для логина"))
                    continue

                # 3. Сохраняем в базу
                author, created = Author.objects.update_or_create(
                    username=username,
                    defaults={
                        'last_name': last_name,
                        'first_name': first_name,
                        'patronymic': patronymic,
                        'password': 123,
                        'researcher_id': item.get('researcher_id'),
                        'scopus_id': item.get('scopus_id'),
                        'orcid': item.get('orcid'),
                        'google_scholar': item.get('google_scholar'),
                    }
                )

                if created:
                    author.save()
                    self.stdout.write(self.style.SUCCESS(f"Добавлен: {full_name}"))
                else:
                    self.stdout.write(f"Обновлен: {full_name}")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка в строке {item.get('full_name')}: {e}"))

        self.stdout.write(self.style.SUCCESS('Импорт завершен успешно!'))

