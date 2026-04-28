from django.core.management import BaseCommand
from django.utils.dateparse import parse_date
from main_app.models import Journal  # ЗАМЕНИТЕ your_app на ваше приложение


class Command(BaseCommand):

    def handle(self, *args, **options):
        journals = Journal.objects.all()
        r = 0
        for journal in journals:
            journal.title = journal.title.title()
            journal.save()
            r += 1
            if r % 100 == 0:
                print(r)
