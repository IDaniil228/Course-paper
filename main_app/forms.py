from django import forms
from .models import Article, Author, CitationDatabase

class ArticleForm(forms.ModelForm):
    # Поле ввода журнала (ручная обработка)
    journal_text = forms.CharField(
        max_length=500,
        label='Журнал',
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Начните вводить название...',
            'autocomplete': 'off'
        })
    )
    journal_hidden = forms.CharField(widget=forms.HiddenInput(), required=False)

    authors = forms.ModelMultipleChoiceField(
        queryset=Author.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'select2-authors'}),
        label='Авторы',
        help_text='Выберите всех авторов статьи (включая себя)'
    )
    citation_databases = forms.ModelMultipleChoiceField(
        queryset=CitationDatabase.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'select2-databases'}),
        label='Базы цитирования',
        required=False
    )

    class Meta:
        model = Article
        fields = [
            'title', 'publish_year', 'full_biblio_description',
            'doi', 'scientific_field'
        ]
        labels = {
            'title': 'Название статьи',
            'publish_year': 'Год публикации',
            'scientific_field': 'Научное направление',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Задаём, как будет отображаться каждый автор в списке и тегах
        self.fields['authors'].label_from_instance = self.author_label

    @staticmethod
    def author_label(obj):
        """Формирует строку: Фамилия И.О. (username)"""
        parts = [obj.last_name, obj.first_name]
        if obj.patronymic:
            parts.append(obj.patronymic)
        full_name = ' '.join(parts)
        return f"{full_name}"