"""
Management команда для генерации расписания через CLI
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext as _

from apps.groups.models import StudyGroups
from apps.studies.schedule_generator import (
    generate_schedule_for_groups,
    validate_generated_schedule,
    get_schedule_statistics,
)


class Command(BaseCommand):
    help = 'Генерация расписания для учебных групп'

    def add_arguments(self, parser):
        parser.add_argument(
            '--groups',
            nargs='+',
            type=int,
            required=True,
            help='ID групп для генерации расписания (например: --groups 1 2 3)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить существующее расписание перед генерацией'
        )
        parser.add_argument(
            '--prefer-evening',
            action='store_true',
            help='Приоритет вечерних пар (по умолчанию утренние)'
        )
        parser.add_argument(
            '--validate-only',
            action='store_true',
            help='Только проверить расписание без генерации'
        )
        parser.add_argument(
            '--stats-only',
            action='store_true',
            help='Только показать статистику расписания'
        )

    def handle(self, *args, **options):
        group_ids = options['groups']
        clear_existing = options['clear']
        prefer_morning = not options['prefer_evening']
        validate_only = options['validate_only']
        stats_only = options['stats_only']

        # Проверяем существование групп
        existing_groups = StudyGroups.objects.filter(id__in=group_ids)
        if existing_groups.count() != len(group_ids):
            missing_ids = set(group_ids) - set(existing_groups.values_list('id', flat=True))
            raise CommandError(f'Группы с ID {missing_ids} не найдены')

        self.stdout.write(self.style.SUCCESS(f'\nРабота с группами: {[g.title for g in existing_groups]}'))

        # Режим только статистики
        if stats_only:
            self.show_statistics(group_ids)
            return

        # Режим только валидации
        if validate_only:
            self.validate_schedule(group_ids)
            return

        # Генерация расписания
        self.generate_schedule(group_ids, clear_existing, prefer_morning)


    def generate_schedule(self, group_ids, clear_existing, prefer_morning):
        """Генерация расписания"""
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.WARNING('ГЕНЕРАЦИЯ РАСПИСАНИЯ'))
        self.stdout.write('='*70 + '\n')

        if clear_existing:
            self.stdout.write(self.style.WARNING('⚠ Существующее расписание будет очищено!'))

        preference = 'утренних' if prefer_morning else 'вечерних'
        self.stdout.write(f'Приоритет: {preference} пар\n')

        # Запускаем генерацию
        success, messages, statistics = generate_schedule_for_groups(
            group_ids=group_ids,
            clear_existing=clear_existing,
            prefer_morning=prefer_morning
        )

        # Выводим сообщения
        for message in messages:
            if 'успешно' in message.lower():
                self.stdout.write(self.style.SUCCESS(f'✓ {message}'))
            elif 'ошибка' in message.lower() or 'конфликт' in message.lower():
                self.stdout.write(self.style.ERROR(f'✗ {message}'))
            else:
                self.stdout.write(f'  {message}')

        # Статистика
        self.stdout.write('\n' + '-'*70)
        self.stdout.write(self.style.WARNING('СТАТИСТИКА:'))
        self.stdout.write(f"  Групп: {statistics.get('total_groups', 0)}")
        self.stdout.write(f"  Предметов всего: {statistics.get('total_subjects', 0)}")
        self.stdout.write(f"  Назначено слотов: {statistics.get('assigned_subjects', 0)}")
        self.stdout.write(f"  Конфликтов: {statistics.get('conflicts', 0)}")
        self.stdout.write('-'*70 + '\n')

        if success:
            self.stdout.write(self.style.SUCCESS('✓ Расписание успешно сгенерировано!\n'))
            # Автоматическая валидация
            self.stdout.write('Выполняется валидация...')
            self.validate_schedule(group_ids)
        else:
            self.stdout.write(self.style.ERROR('✗ Не удалось сгенерировать расписание\n'))
            raise CommandError('Генерация расписания не удалась. См. сообщения выше.')

    def validate_schedule(self, group_ids):
        """Валидация расписания"""
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.WARNING('ВАЛИДАЦИЯ РАСПИСАНИЯ'))
        self.stdout.write('='*70 + '\n')

        is_valid, conflicts = validate_generated_schedule(group_ids)

        if is_valid:
            self.stdout.write(self.style.SUCCESS('✓ ' + conflicts[0]))
        else:
            self.stdout.write(self.style.ERROR(f'✗ Обнаружено конфликтов: {len(conflicts)}\n'))
            for i, conflict in enumerate(conflicts, 1):
                self.stdout.write(self.style.ERROR(f'  {i}. {conflict}'))

        self.stdout.write('')

    def show_statistics(self, group_ids):
        """Показать статистику расписания"""
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.WARNING('СТАТИСТИКА РАСПИСАНИЯ'))
        self.stdout.write('='*70 + '\n')

        stats = get_schedule_statistics(group_ids)

        self.stdout.write(f"📊 Групп: {stats['total_groups']}")
        self.stdout.write(f"📚 Предметов всего: {stats['total_subjects']}")
        self.stdout.write(f"✓ С расписанием: {stats['subjects_with_schedule']}")
        self.stdout.write(f"✗ Без расписания: {stats['subjects_without_schedule']}")
        self.stdout.write(f"📅 Всего слотов: {stats['total_schedule_slots']}")
        self.stdout.write(f"📈 Среднее слотов/предмет: {stats['average_slots_per_subject']}")
        
        # Процент заполненности
        if stats['total_subjects'] > 0:
            fill_percent = (stats['subjects_with_schedule'] / stats['total_subjects']) * 100
            self.stdout.write(f"📊 Заполненность: {fill_percent:.1f}%")
        
        self.stdout.write('')

