from django.core.management import BaseCommand
from django.utils.dateparse import parse_date
from main_app.models import Journal, Author  # ЗАМЕНИТЕ your_app на ваше приложение


class Command(BaseCommand):

    def handle(self, *args, **options):
        user = Author.objects.get(id=94)
        user.set_password(user.password)
        user.save(update_fields=['password'])
