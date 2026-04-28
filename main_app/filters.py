import django_filters
from .models import Article, CitationDatabase, Journal

class ArticleFilter(django_filters.FilterSet):
    # Фильтр по уровню через связь с журналом
    LEVEL_CHOICES = (
        (1, 'Q1 (1 уровень)'),
        (2, 'Q2 (2 уровень)'),
        (3, 'Q3 (3 уровень)'),
        (4, 'Q4 (4 уровень)'),
    )
    level = django_filters.ChoiceFilter(
        field_name='journal__level',
        choices=LEVEL_CHOICES,
        label="Уровень журнала"
    )

    # Фильтр по базе цитирования (выпадающий список)
    citation_databases = django_filters.ModelChoiceFilter(
        queryset=CitationDatabase.objects.all(),
        label="База цитирования"
    )

    # Фильтр по году (можно сделать точный выбор или диапазон)
    publish_year = django_filters.NumberFilter(
        field_name='publish_year',
        label="Год публикации"
    )

    class Meta:
        model = Article
        fields = ['level', 'citation_databases', 'publish_year']