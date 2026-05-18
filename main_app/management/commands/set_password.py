from django.contrib.auth.hashers import make_password
from django.core.management import BaseCommand
from django.utils.dateparse import parse_date
from main_app.models import Journal, Author


class Command(BaseCommand):

    def handle(self, *args, **options):
        users = Author.objects.all()
        i = 0
        for user in users:
            user.password = make_password("123")
            i += 1
            print(i)

        Author.objects.bulk_update(users, ['password'])