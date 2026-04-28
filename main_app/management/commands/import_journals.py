import pandas as pd
import numpy as np
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_date
from main_app.models import Journal  # ЗАМЕНИТЕ your_app на ваше приложение


class Command(BaseCommand):
    help = 'Импорт данных: расчет уровня (2025 > 2023) и логика поля state'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Путь к файлу CSV')

    def handle(self, *args, **options):
        r = 0
        file_path = options['csv_file']

        try:
            # Читаем CSV
            df = pd.read_csv(file_path)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка чтения: {e}"))
            return

        # 1. Общая логика для булевых полей (Scopus, WoS и др.)
        def to_bool(val):
            if pd.isna(val) or str(val).strip() == '': return None
            s = str(val).strip().lower()
            return s in ['true', '1', '1.0', 'yes', 'y', 'да']

        # 2. Специфическая логика для вашего поля state (из текста в bool)
        def get_state_as_bool(val):
            # Условие:
            # Если пусто (NaN) -> True (входит)
            # Если "warning" -> True (входит)
            # Если "discontinued" -> False (не входит)
            if pd.isna(val) or str(val).strip() == '':
                return True

            s = str(val).strip().lower()
            if s == 'discontinued':
                return False
            if s == 'warning':
                return True

            # На всякий случай: если там какой-то другой текст, считаем что входит
            return True

        # 3. Логика выбора уровня (2025 в приоритете над 2023)
        def get_final_level(row):
            l25 = row.get('level_2025')
            l23 = row.get('level_2023')

            # Проверяем 2025
            if pd.notna(l25) and str(l25).strip().lower() not in ['nan', '']:
                try:
                    return int(float(l25))
                except:
                    pass

            # Проверяем 2023
            if pd.notna(l23) and str(l23).strip().lower() not in ['nan', '']:
                try:
                    return int(float(l23))
                except:
                    pass

            return None

        def clean_str(val):
            if pd.isna(val) or str(val).strip().lower() in ['nan', '']:
                return None
            return str(val).strip()

        self.stdout.write(f"Обработка {len(df)} строк...")

        for index, row in df.iterrows():
            try:
                # Рассчитываем итоговые значения для модели
                final_level = get_final_level(row)
                state_bool = get_state_as_bool(row.get('state'))

                data = {
                    "title":clean_str(row.get('title')),
                    'level': final_level,
                    'state': state_bool,  # Поле state в модели теперь Boolean
                    'wos_cc': to_bool(row.get('wos_cc')),
                    'scopus': to_bool(row.get('scopus')),
                    'srcid': clean_str(row.get('srcid')),
                    'rsci': to_bool(row.get('rsci')),
                    'open_access_doaj': to_bool(row.get('Open_Access_DOAJ')),
                    'doaj_id': clean_str(row.get('doaj_id')),
                    'humanities_erih_plus': to_bool(row.get('Humanities_ERIH_PLUS')),
                    'physics_inspec': to_bool(row.get('Physics_Inspec')),
                    'comp_science_dblp': to_bool(row.get('Comp_Science_DBLP')),
                    'medicine_medline': to_bool(row.get('Medicine_Medline')),
                    'biomedicine_embase': to_bool(row.get('Biomedicine_Embase')),
                    'agriculture_agricola': to_bool(row.get('Agriculture_Agricola')),
                    'agriculture_cab': to_bool(row.get('Agriculture_CAB')),
                    'engineering_compendex': to_bool(row.get('Engineering_Compendex')),
                    'geology_georef': to_bool(row.get('Geology_GeoRef')),
                    'geography_geobase': to_bool(row.get('Geography_Geobase')),
                    'chemical_ref_index': to_bool(row.get('Chemical_Ref_Index')),
                    'food_science_fsta': to_bool(row.get('Food_Science_FSTA')),
                    'health_safety_abs': to_bool(row.get('Health_Safety_Abs')),
                    'poultry_science_wpsa': to_bool(row.get('Poultry_Science_WPSA')),
                    'sociology_socabs': to_bool(row.get('Sociology_SocAbs')),
                    'chemistry_index': to_bool(row.get('Chemistry_Index')),
                    'zoology_record': to_bool(row.get('Zoology_Record')),
                    'biology_abstracts': to_bool(row.get('Biology_Abstracts')),
                    'petroleum_index': to_bool(row.get('Petroleum_Index')),
                    'date_accepted': parse_date(str(row.get('date_accepted'))) if pd.notna(
                        row.get('date_accepted')) else None,
                    'date_discontinued': parse_date(str(row.get('date_discontinued'))) if pd.notna(
                        row.get('date_discontinued')) else None,
                }
                r += 1
                if r % 300 == 0:
                    print(r)
                # Обновляем или создаем запись
                Journal.objects.update_or_create(
                    issns=clean_str(row.get('issns')),
                    defaults=data
                )

            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Ошибка в строке {index}: {e}"))

        self.stdout.write(self.style.SUCCESS('Импорт завершен успешно.'))