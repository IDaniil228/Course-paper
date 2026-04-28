from django.core.management import BaseCommand
from django.utils.dateparse import parse_date
from main_app.models import Journal  # ЗАМЕНИТЕ your_app на ваше приложение


class Command(BaseCommand):

    def handle(self, *args, **options):
        journals = Journal.objects.filter(id__gt=31552)
        count = journals.count()

        if count > 0:
            print(f"Найдено {count} журналов для удаления")
            journals.delete()
        else:
            print("Нет журналов для удаления")