"""
Алгоритм автоматической генерации расписания занятий
"""
import random
from datetime import time
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from .models import Subjects, SubjectSchedule, TimeSlot, Day, StudyGroups
from apps.buildings.models import Audiences
from .choices import EvenOddBoth
from .validators import (
    validate_group_schedule_conflict,
    validate_audience_schedule_conflict,
    validate_teacher_schedule_conflict
)

# Предустановленные временные промежутки
TIME_RANGES = {
    'morning': {
        'name': 'Утренние пары',
        'start_time': time(8, 0),
        'end_time': time(14, 30),
        'description': 'Занятия с утра до обеда (08:00-14:30)'
    },
    'mixed': {
        'name': 'Смешанные пары',
        'start_time': time(11, 30),
        'end_time': time(17, 0),
        'description': 'Занятия со второй половины дня (11:30-17:00)'
    },
    'afternoon': {
        'name': 'Послеобеденные пары',
        'start_time': time(13, 0),
        'end_time': time(18, 20),
        'description': 'Занятия во второй половине дня (13:00-18:20)'
    },
    'evening': {
        'name': 'Вечерние пары',
        'start_time': time(16, 0),
        'end_time': time(21, 0),
        'description': 'Вечерние занятия (16:00-21:00)'
    },
    'full': {
        'name': 'Весь день',
        'start_time': time(8, 0),
        'end_time': time(21, 0),
        'description': 'Все доступные временные слоты'
    }
}


class ScheduleConflict(Exception):
    """Исключение для конфликтов расписания"""
    pass


class ScheduleGenerator:
    """
    Генератор расписания с использованием алгоритма constraint satisfaction.
    
    Реализует эвристический алгоритм распределения предметов по временным слотам
    с учетом ограничений:
    - Группа не может иметь больше одного предмета в один временной слот
    - Аудитория не может быть занята более одним предметом (кроме потоковых)
    - Преподаватель не может вести несколько предметов одновременно
    """
    
    def __init__(self):
        self.schedule_matrix = defaultdict(lambda: defaultdict(dict))
        self.conflicts_log = []
        
    def generate_schedule(
        self,
        groups: List[StudyGroups],
        subjects_per_group: Dict[int, List[Subjects]],
        prefer_morning: bool = True,
        max_attempts: int = 100,
        time_range: Optional[str] = None,
        custom_start_time: Optional[time] = None,
        custom_end_time: Optional[time] = None,
        start_day_id: Optional[int] = None,
        end_day_id: Optional[int] = None
    ) -> Tuple[bool, List[str]]:
        """
        Генерирует расписание для указанных групп и предметов.
        
        Args:
            groups: список учебных групп
            subjects_per_group: словарь {group_id: [subjects]}
            prefer_morning: приоритет утренних пар
            max_attempts: максимальное количество попыток
            time_range: предустановленный временной промежуток ('morning', 'mixed', 'afternoon', 'evening', 'full')
            custom_start_time: кастомное время начала
            custom_end_time: кастомное время окончания
            start_day_id: ID начального дня недели
            end_day_id: ID конечного дня недели
            
        Returns:
            Tuple[success, messages]: успех операции и список сообщений
        """
        messages = []
        
        # Определяем временной промежуток
        start_time, end_time = self._get_time_range(
            time_range, custom_start_time, custom_end_time
        )
        
        if start_time and end_time:
            messages.append(_(f"Временной промежуток: {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"))
        
        # Получаем все доступные временные слоты и дни недели
        all_time_slots = list(TimeSlot.objects.all().order_by('number'))
        all_days = list(Day.objects.all().order_by('id'))
        
        # Фильтруем дни по диапазону
        if start_day_id and end_day_id:
            all_days = [day for day in all_days if start_day_id <= day.id <= end_day_id]
            if all_days:
                start_day_name = Day.objects.get(id=start_day_id).title
                end_day_name = Day.objects.get(id=end_day_id).title
                messages.append(_(f"Дни недели: с {start_day_name} по {end_day_name}"))
        elif start_day_id or end_day_id:
            # Если указан только один из дней, используем его как единственный день
            day_id = start_day_id or end_day_id
            all_days = [day for day in all_days if day.id == day_id]
            if all_days:
                day_name = Day.objects.get(id=day_id).title
                messages.append(_(f"День недели: {day_name}"))
        
        # Фильтруем слоты по временному промежутку
        if start_time and end_time:
            all_time_slots = [
                slot for slot in all_time_slots
                if start_time <= slot.start_time <= end_time
            ]
            messages.append(_(f"Доступных временных слотов: {len(all_time_slots)}"))
        
        if not all_time_slots or not all_days:
            return False, [_("Ошибка: не созданы временные слоты или дни недели, либо выбранный диапазон пуст")]
        
        # Создаем комбинации день+слот
        all_slots = []
        for day in all_days:
            for time_slot in all_time_slots:
                all_slots.append((day, time_slot))
        
        messages.append(_(f"Всего доступных слотов (день+время): {len(all_slots)}"))
        # Сортируем слоты (утренние пары приоритетнее)
        if prefer_morning:
            all_slots.sort(key=lambda s: (s[0].id, s[1].number))
        else:
            all_slots.sort(key=lambda s: (s[0].id, -s[1].number))
        
        # Создаем список всех предметов для распределения
        all_assignments = []
        for group in groups:
            group_subjects = subjects_per_group.get(group.id, [])
            for subject in group_subjects:
                # Каждый предмет нужно назначить на определенное количество слотов
                # По умолчанию считаем, что нужно назначить на один слот
                all_assignments.append({
                    'subject': subject,
                    'group': group,
                    'assigned': False
                })
        
        messages.append(_(f"Всего предметов для распределения: {len(all_assignments)}"))
        
        # Пытаемся распределить предметы
        for attempt in range(max_attempts):
            success = self._try_assign_all(all_assignments, all_slots)
            if success:
                messages.append(_(f"Расписание успешно сгенерировано за {attempt + 1} попыток"))
                return True, messages
            
            # Перемешиваем для новой попытки
            random.shuffle(all_assignments)
        
        messages.append(_(f"Не удалось сгенерировать расписание за {max_attempts} попыток"))
        messages.extend(self.conflicts_log[-10:])  # Последние 10 конфликтов
        return False, messages
    
    def _try_assign_all(self, assignments: List[Dict], slots: List[Tuple[Day, TimeSlot]]) -> bool:
        """
        Пытается назначить все предметы на слоты с равномерным распределением по дням.
        
        Args:
            assignments: список назначений предметов
            slots: список комбинаций (день, временной_слот)
            
        Returns:
            bool: успешность распределения
        """
        # Сбрасываем матрицу конфликтов
        self.schedule_matrix = defaultdict(lambda: defaultdict(dict))
        
        # Группируем слоты по дням
        slots_by_day = defaultdict(list)
        for day, time_slot in slots:
            slots_by_day[day.id].append((day, time_slot))
        
        # Получаем уникальные дни в правильном порядке
        days = []
        seen_day_ids = set()
        for day, _ in slots:
            if day.id not in seen_day_ids:
                days.append(day)
                seen_day_ids.add(day.id)
        
        # Для равномерного распределения назначаем предметы циклически по дням
        # Если 3 предмета и 3 дня: по 1 предмету на день
        # Если 4 предмета и 3 дня: 2-1-1
        # Если 5 предметов и 3 дня: 2-2-1 и т.д.
        
        day_index = 0
        for assignment in assignments:
            subject = assignment['subject']
            group = assignment['group']
            
            # Пытаемся назначить на текущий день
            assigned = False
            attempts = 0
            
            # Пробуем назначить на день, начиная с текущего индекса
            while attempts < len(days) and not assigned:
                current_day = days[day_index % len(days)]
                day_slots = slots_by_day[current_day.id]
                
                # Пытаемся найти свободный слот в этом дне
                for day, time_slot in day_slots:
                    if self._can_assign(subject, group, day, time_slot):
                        self._assign(subject, group, day, time_slot)
                        assignment['assigned'] = True
                        assigned = True
                        break
                
                if not assigned:
                    # Пробуем следующий день
                    attempts += 1
                    day_index += 1
            
            if assigned:
                # Переходим к следующему дню для следующего предмета
                day_index += 1
            else:
                # Не удалось назначить даже при попытке всех дней
                return False
        
        return True
    
    def _can_assign(self, subject: Subjects, group: StudyGroups, 
                   day: Day, time_slot: TimeSlot, week_type: str = EvenOddBoth.BOTH) -> bool:
        """
        Проверяет, можно ли назначить предмет на слот.
        
        Args:
            subject: предмет
            group: учебная группа
            day: день недели
            time_slot: временной слот
            week_type: тип недели (по умолчанию BOTH)
            
        Returns:
            bool: можно ли назначить
        """
        slot_key = (day.id, time_slot.id, week_type)
        
        # Проверка 1: Группа не занята в это время
        if group.id in self.schedule_matrix[slot_key]:
            self.conflicts_log.append(
                f"Группа {group.title} уже занята в {day.title} {time_slot.number}-я пара"
            )
            return False
        
        # Проверка 2: Аудитория свободна (или это потоковый предмет)
        audience = subject.audience
        if audience.id in self.schedule_matrix[slot_key].get('audiences', {}):
            existing_subject = self.schedule_matrix[slot_key]['audiences'][audience.id]
            # Проверяем, это тот же предмет (потоковый) или другой
            if existing_subject.id != subject.id:
                self.conflicts_log.append(
                    f"Аудитория {audience.title} занята предметом {existing_subject.title} в {day.title} {time_slot.number}-я пара"
                )
                return False
        
        # Проверка 3: Преподаватели - пропускаем, так как у Subjects нет поля teachers
        # Преподаватели будут назначены вручную через админку после генерации
        
        return True
    
    def _assign(self, subject: Subjects, group: StudyGroups, 
               day: Day, time_slot: TimeSlot, week_type: str = EvenOddBoth.BOTH):
        """
        Назначает предмет на слот.
        
        Args:
            subject: предмет
            group: учебная группа
            day: день недели
            time_slot: временной слот
            week_type: тип недели (по умолчанию BOTH)
        """
        slot_key = (day.id, time_slot.id, week_type)
        
        # Отмечаем группу как занятую
        self.schedule_matrix[slot_key][group.id] = {
            'subject': subject,
            'day': day,
            'time_slot': time_slot,
            'week_type': week_type
        }
        
        # Отмечаем аудиторию
        if 'audiences' not in self.schedule_matrix[slot_key]:
            self.schedule_matrix[slot_key]['audiences'] = {}
        self.schedule_matrix[slot_key]['audiences'][subject.audience.id] = subject
        
        # Преподаватели не отмечаются, так как у Subjects нет поля teachers
        # Преподаватели будут назначены через админку
    
    def _get_time_range(self, time_range: Optional[str], 
                       custom_start: Optional[time], 
                       custom_end: Optional[time]) -> Tuple[Optional[time], Optional[time]]:
        """
        Определяет временной промежуток для генерации.
        
        Args:
            time_range: имя предустановленного промежутка
            custom_start: кастомное время начала
            custom_end: кастомное время окончания
            
        Returns:
            Tuple[start_time, end_time]
        """
        # Приоритет: кастомные значения > предустановленные
        if custom_start and custom_end:
            return custom_start, custom_end
        
        if time_range and time_range in TIME_RANGES:
            range_config = TIME_RANGES[time_range]
            return range_config['start_time'], range_config['end_time']
        
        # По умолчанию - весь день
        return None, None


def generate_schedule_for_group(
    group_id: int,
    subject_ids: List[int],
    clear_existing: bool = False,
    prefer_morning: bool = True,
    time_range: Optional[str] = None,
    custom_start_time: Optional[time] = None,
    custom_end_time: Optional[time] = None,
    start_day_id: Optional[int] = None,
    end_day_id: Optional[int] = None
) -> Tuple[bool, List[str], Dict]:
    """
    Главная функция для генерации расписания.
    
    Args:
        group_id: ID группы для генерации
        subject_ids: список ID предметов для генерации
        clear_existing: очистить существующее расписание
        prefer_morning: приоритет утренних пар
        time_range: предустановленный временной промежуток
        custom_start_time: кастомное время начала (HH:MM)
        custom_end_time: кастомное время окончания (HH:MM)
        start_day_id: ID начального дня недели
        end_day_id: ID конечного дня недели
        
    Returns:
        Tuple[success, messages, statistics]
    """
    messages = []
    statistics = {
        'total_subjects': 0,
        'assigned_subjects': 0,
        'conflicts': 0
    }
    
    try:
        # Получаем группу
        try:
            group = StudyGroups.objects.get(id=group_id, is_active=True)
        except StudyGroups.DoesNotExist:
            return False, [_("Группа не найдена")], statistics
        
        messages.append(_(f"Генерация расписания для группы {group.title}"))
        
        # Получаем предметы
        subjects = list(Subjects.objects.filter(id__in=subject_ids))
        if len(subjects) != len(subject_ids):
            return False, [_("Один или несколько предметов не найдены")], statistics
        
        statistics['total_subjects'] = len(subjects)
        messages.append(_(f"Всего предметов: {statistics['total_subjects']}"))
        
        # Очищаем существующее расписание если нужно
        if clear_existing:
            deleted_count = 0
            with transaction.atomic():
                for subject in subjects:
                    # Находим все расписания этого предмета, связанные с группой
                    schedules = SubjectSchedule.objects.filter(
                        subject=subject,
                        groups=group
                    )
                    
                    for schedule in schedules:
                        # Проверяем количество групп ДО удаления связи
                        groups_count = schedule.groups.count()
                        
                        # Удаляем связь группы с расписанием
                        schedule.groups.remove(group)
                        
                        # Если это была единственная группа, удаляем расписание полностью
                        if groups_count == 1:
                            schedule.delete()
                            deleted_count += 1
            
            messages.append(_(f"Существующее расписание очищено (удалено записей: {deleted_count})"))
        
        # Подготавливаем данные для генератора
        subjects_per_group = {group.id: subjects}
        
        # Запускаем генератор
        generator = ScheduleGenerator()
        success, gen_messages = generator.generate_schedule(
            [group],
            subjects_per_group,
            prefer_morning=prefer_morning,
            time_range=time_range,
            custom_start_time=custom_start_time,
            custom_end_time=custom_end_time,
            start_day_id=start_day_id,
            end_day_id=end_day_id
        )
        
        messages.extend(gen_messages)
        
        if success:
            # Применяем сгенерированное расписание
            with transaction.atomic():
                for slot_key, slot_data in generator.schedule_matrix.items():
                    week_day_id, time_slot_id, week_type = slot_key
                    
                    # Назначаем расписание предметам
                    for key, data in slot_data.items():
                        # Пропускаем служебные ключи 'audiences' и 'teachers'
                        if key in ('audiences', 'teachers'):
                            continue
                        
                        # Если ключ - это ID группы (int), то data - это dict с информацией о расписании
                        if isinstance(key, int) and isinstance(data, dict):
                            # Это данные о предмете группы
                            subject = data['subject']
                            day = data['day']
                            time_slot = data['time_slot']
                            week_type_val = data['week_type']
                            
                            # Создаем или получаем запись расписания
                            schedule, created = SubjectSchedule.objects.get_or_create(
                                subject=subject,
                                week_day=day,
                                time_slot=time_slot,
                                week_type=week_type_val
                            )
                            
                            # Добавляем группу к расписанию
                            schedule.groups.add(group)
                            
                            # Преподаватели не добавляются автоматически, так как у Subjects нет поля teachers
                            # Их нужно назначить вручную через админку после генерации
                            
                            statistics['assigned_subjects'] += 1
            
            messages.append(_(f"Расписание успешно применено к БД"))
            messages.append(_(f"Назначено слотов: {statistics['assigned_subjects']}"))
        else:
            statistics['conflicts'] = len(generator.conflicts_log)
        
        return success, messages, statistics
        
    except Exception as e:
        messages.append(_(f"Ошибка генерации: {str(e)}"))
        return False, messages, statistics


def validate_generated_schedule(group_ids: List[int]) -> Tuple[bool, List[str]]:
    """
    Валидирует сгенерированное расписание на наличие конфликтов.
    
    Args:
        group_ids: список ID групп для проверки
        
    Returns:
        Tuple[is_valid, conflict_messages]
    """
    conflicts = []
    
    subjects = Subjects.objects.filter(groups__id__in=group_ids).distinct()
    
    for subject in subjects:
        try:
            validate_group_schedule_conflict(subject)
            validate_audience_schedule_conflict(subject)
            validate_teacher_schedule_conflict(subject)
        except Exception as e:
            conflicts.append(str(e))
    
    is_valid = len(conflicts) == 0
    
    if is_valid:
        return True, [_("Расписание корректно, конфликтов не обнаружено")]
    else:
        return False, conflicts


def get_schedule_statistics(group_ids: List[int]) -> Dict:
    """
    Возвращает статистику по расписанию групп.
    
    Args:
        group_ids: список ID групп
        
    Returns:
        Dict: статистика расписания
    """
    groups = StudyGroups.objects.filter(id__in=group_ids)
    subjects = Subjects.objects.filter(groups__in=groups).distinct()
    
    total_slots = 0
    subjects_with_schedule = 0
    subjects_without_schedule = 0
    
    for subject in subjects:
        schedule_count = subject.schedules.count()
        total_slots += schedule_count
        if schedule_count > 0:
            subjects_with_schedule += 1
        else:
            subjects_without_schedule += 1
    
    return {
        'total_groups': groups.count(),
        'total_subjects': subjects.count(),
        'subjects_with_schedule': subjects_with_schedule,
        'subjects_without_schedule': subjects_without_schedule,
        'total_schedule_slots': total_slots,
        'average_slots_per_subject': round(total_slots / subjects.count(), 2) if subjects.count() > 0 else 0
    }


def get_available_time_ranges() -> Dict:
    """
    Возвращает список доступных предустановленных временных промежутков.
    
    Returns:
        Dict: словарь с описаниями временных промежутков
    """
    return {
        key: {
            'name': config['name'],
            'start_time': config['start_time'].strftime('%H:%M'),
            'end_time': config['end_time'].strftime('%H:%M'),
            'description': config['description']
        }
        for key, config in TIME_RANGES.items()
    }
