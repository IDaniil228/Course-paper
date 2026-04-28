from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

from django.db import models


class Journal(models.Model):
    # --- Основная информация ---
    title = models.TextField(
        null=True, blank=True, default=None,
        verbose_name="Название журнала",
        help_text="Полное официальное название научного издания"
    )
    issns = models.CharField(
        max_length=100, null=True, blank=True, default=None,
        verbose_name="ISSN(s)",
        help_text="Международные стандартные серийные номера (p-ISSN, e-ISSN)"
    )

    state = models.BooleanField(
        null=True, blank=True, default=None,
        help_text="Входит ли в белый список"
    )

    level = models.IntegerField(
        null=True, blank=True, default=None,
        verbose_name="Уровень 2025",
        help_text="утвержденная категория (q1 q2 q3 q4)"
    )

    # --- Глобальные индексы цитирования ---
    # Используем BooleanField с null=True, чтобы дефолтом было None (неизвестно)
    wos_cc = models.BooleanField(
        null=True, blank=True, default=None,
        verbose_name="Web of Science CC",
        help_text="Входит ли журнал в Core Collection Web of Science"
    )
    scopus = models.BooleanField(
        null=True, blank=True, default=None,
        verbose_name="Scopus",
        help_text="Индексируется ли журнал в базе Scopus"
    )
    srcid = models.CharField(
        max_length=50, null=True, blank=True, default=None,
        verbose_name="Scopus SourceID",
        help_text="Уникальный идентификатор журнала в системе Scopus"
    )
    rsci = models.BooleanField(
        null=True, blank=True, default=None,
        verbose_name="RSCI (РИНЦ)",
        help_text="Входит ли журнал в Russian Science Citation Index"
    )

    # --- Специализированные базы данных (Тематические индексы) ---
    open_access_doaj = models.BooleanField(
        null=True, blank=True, default=None,
        verbose_name="Open Access (DOAJ)",
        help_text="Журнал открытого доступа, индексируемый в DOAJ"
    )
    doaj_id = models.CharField(
        max_length=100, null=True, blank=True, default=None,
        verbose_name="DOAJ ID",
        help_text="Идентификатор журнала в базе DOAJ"
    )
    humanities_erih_plus = models.BooleanField(
        null=True, blank=True, default=None,
        verbose_name="Humanities (ERIH PLUS)",
        help_text="Европейский индекс для гуманитарных и социальных наук"
    )
    physics_inspec = models.BooleanField(
        null=True, blank=True, default=None,
        verbose_name="Physics (Inspec)",
        help_text="База данных по физике и компьютерным наукам"
    )
    comp_science_dblp = models.BooleanField(
        null=True, blank=True, default=None,
        verbose_name="Comp. Science (DBLP)",
        help_text="Библиография по компьютерным наукам"
    )
    medicine_medline = models.BooleanField(
        null=True, blank=True, default=None,
        verbose_name="Medicine (Medline)",
        help_text="Крупнейшая база данных по медицине и биологии"
    )
    biomedicine_embase = models.BooleanField(
        null=True, blank=True, default=None,
        verbose_name="Biomedicine (Embase)",
        help_text="База данных по биомедицине и фармакологии"
    )
    agriculture_agricola = models.BooleanField(
        null=True, blank=True, default=None,
        verbose_name="Agriculture (Agricola)",
        help_text="База данных Национальной сельскохозяйственной библиотеки США"
    )
    agriculture_cab = models.BooleanField(
        null=True, blank=True, default=None,
        verbose_name="Agriculture (CAB Abstracts)",
        help_text="Прикладные науки о жизни и сельское хозяйство"
    )
    engineering_compendex = models.BooleanField(
        null=True, blank=True, default=None,
        verbose_name="Engineering (Compendex)",
        help_text="Наиболее полная база инженерных публикаций"
    )
    geology_georef = models.BooleanField(
        null=True, blank=True, default=None,
        verbose_name="Geology (GeoRef)",
        help_text="База данных Американского геологического института"
    )
    geography_geobase = models.BooleanField(
        null=True, blank=True, default=None,
        verbose_name="Geography (Geobase)",
        help_text="Междисциплинарная база данных о Земле"
    )
    chemical_ref_index = models.BooleanField(
        null=True, blank=True, default=None,
        verbose_name="Chemical Ref. Index",
        help_text="Химический справочный индекс"
    )
    food_science_fsta = models.BooleanField(
        null=True, blank=True, default=None,
        verbose_name="Food Science (FSTA)",
        help_text="База данных по пищевым наукам и технологиям"
    )
    health_safety_abs = models.BooleanField(
        null=True, blank=True, default=None,
        verbose_name="Health & Safety Abs.",
        help_text="Абстракты по гигиене и безопасности труда"
    )
    poultry_science_wpsa = models.BooleanField(
        null=True, blank=True, default=None,
        verbose_name="Poultry Science (WPSA)",
        help_text="База публикаций по птицеводству"
    )
    sociology_socabs = models.BooleanField(
        null=True, blank=True, default=None,
        verbose_name="Sociology (SocAbs)",
        help_text="База данных по социологии и социальным наукам"
    )
    chemistry_index = models.BooleanField(
        null=True, blank=True, default=None,
        verbose_name="Chemistry Index",
        help_text="Специализированный индекс химических изданий"
    )
    zoology_record = models.BooleanField(
        null=True, blank=True, default=None,
        verbose_name="Zoology Record",
        help_text="База данных по биологии животных и зоологии"
    )
    biology_abstracts = models.BooleanField(
        null=True, blank=True, default=None,
        verbose_name="Biology Abstracts",
        help_text="Аннотации по биологическим наукам"
    )
    petroleum_index = models.BooleanField(
        null=True, blank=True, default=None,
        verbose_name="Petroleum Index",
        help_text="Индекс публикаций в нефтегазовой сфере"
    )

    # --- Даты жизни в списке ---
    date_accepted = models.DateField(
        null=True, blank=True, default=None,
        verbose_name="Дата принятия",
        help_text="Дата включения журнала в Белый список"
    )
    date_discontinued = models.DateField(
        null=True, blank=True, default=None,
        verbose_name="Дата исключения",
        help_text="Дата, после которой журнал перестал входить в Белый список"
    )

    class Meta:
        verbose_name = "Журнал Белого списка"
        verbose_name_plural = "Журналы Белого списка"

    def __str__(self):
        return self.title if self.title else "Без названия"


class CitationDatabase(models.Model):
    """Модель базы цитирования (Scopus, WoS, РИНЦ и т.д.)"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Название базы")

class Author(AbstractUser):
    # Поля first_name и last_name уже есть в AbstractUser,
    # мы добавляем только отчество
    patronymic = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Отчество"
    )

    # Научные идентификаторы
    researcher_id = models.CharField(
        max_length=50, blank=True, null=True,
        verbose_name="Web of Science ResearcherID"
    )
    scopus_id = models.CharField(
        max_length=50, blank=True, null=True,
        verbose_name="Scopus Author ID"
    )
    orcid = models.CharField(
        max_length=20, blank=True, null=True,
        verbose_name="ORCID"
    )
    google_scholar = models.CharField(
        max_length=50, blank=True, null=True,
        verbose_name="Google Scholar ID"
    )


class Article(models.Model):
    """Модель научной статьи"""
    title = models.CharField(
        max_length=1000,
        verbose_name="Заголовок статьи",
        null=True, blank=True, default=None  # Добавлено
    )
    full_biblio_description = models.TextField(
        verbose_name="Полное библиографическое описание",
        null=True, blank=True, default=None  # Добавлено
    )
    publish_year = models.PositiveIntegerField(
        verbose_name="Год публикации",
        null=True, blank=True, default=None  # Добавлено
    )
    doi = models.CharField(
        max_length=255,
        verbose_name="DOI",
        null=True, blank=True, default=None  # Уже было, добавлен default
    )
    scientific_field = models.CharField(
        max_length=255,
        verbose_name="Научное направление",
        null=True, blank=True, default=None  # Добавлено
    )

    # Связи
    journal = models.ForeignKey(
        'Journal',
        on_delete=models.CASCADE,
        related_name="articles",
        verbose_name="Журнал",
        null=True, blank=True, default=None  # Добавлено
    )

    # ПРИМЕЧАНИЕ: ManyToManyField не поддерживает null=True и default на уровне БД,
    # так как это связующая таблица. Достаточно blank=True.
    authors = models.ManyToManyField(
        'Author',
        related_name="articles",
        verbose_name="Авторы",
        blank=True
    )
    citation_databases = models.ManyToManyField(
        'CitationDatabase',
        related_name="articles",
        verbose_name="Базы цитирования",
        blank=True
    )

    # Дополнительные поля из JSON
    total_authors_count = models.PositiveIntegerField(
        verbose_name="Общее количество авторов",
        null=True, blank=True, default=None  # Добавлено
    )
    # Для BooleanField, если нужен именно None, используем null=True
    with_foreign_authors = models.BooleanField(
        verbose_name="С участием иностранных авторов",
        null=True, blank=True, default=None  # Изменено с default=False на None
    )

    def __str__(self):
        return self.title if self.title else "Без заголовка"

    class Meta:
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"