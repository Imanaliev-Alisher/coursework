"""
Валидаторы для проверки конфликтов расписания
"""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from .choices import EvenOddBoth


def validate_group_schedule_conflict(schedule_instance):
    """
    Проверяет, что у группы нет более одного предмета в одно время.
    
    Args:
        schedule_instance: экземпляр модели SubjectSchedule
        
    Raises:
        ValidationError: если найден конфликт расписания группы
    """
    from .models import SubjectSchedule
    
    if not schedule_instance.pk:
        # Новый объект, еще не сохранен - пропускаем валидацию
        return
    
    # Получаем все группы этого расписания
    groups = schedule_instance.groups.all()
    
    for group in groups:
        # Ищем другие предметы у этой группы в это же время
        conflicting_schedules = SubjectSchedule.objects.filter(
            groups=group,
            week_day=schedule_instance.week_day,
            time_slot=schedule_instance.time_slot,
        ).exclude(pk=schedule_instance.pk)
        
        # Фильтрация по типу недели
        if schedule_instance.week_type == EvenOddBoth.BOTH:
            conflicting_schedules = conflicting_schedules.filter(
                Q(week_type=EvenOddBoth.BOTH) |
                Q(week_type=EvenOddBoth.EVEN) |
                Q(week_type=EvenOddBoth.ODD)
            )
        else:
            conflicting_schedules = conflicting_schedules.filter(
                Q(week_type=schedule_instance.week_type) |
                Q(week_type=EvenOddBoth.BOTH)
            )
        
        if conflicting_schedules.exists():
            conflict = conflicting_schedules.first()
            raise ValidationError(
                _(f'Конфликт расписания: группа "{group.title}" уже имеет предмет '
                  f'"{conflict.subject.title}" в {schedule_instance.week_day.title} '
                  f'на {schedule_instance.time_slot.number}-й паре ({schedule_instance.week_type})')
            )


def validate_audience_schedule_conflict(schedule_instance):
    """
    Проверяет, что в аудитории нет более одного предмета в одно время.
    Исключение: потоковые предметы (один предмет для нескольких групп).
    
    Args:
        schedule_instance: экземпляр модели SubjectSchedule
        
    Raises:
        ValidationError: если найдена занятая аудитория
    """
    from .models import SubjectSchedule
    
    if not schedule_instance.pk:
        return
    
    audience = schedule_instance.subject.audience
    
    # Ищем другие предметы в этой аудитории в это же время
    conflicting_schedules = SubjectSchedule.objects.filter(
        subject__audience=audience,
        week_day=schedule_instance.week_day,
        time_slot=schedule_instance.time_slot,
    ).exclude(pk=schedule_instance.pk)
    
    # Фильтрация по типу недели
    if schedule_instance.week_type == EvenOddBoth.BOTH:
        conflicting_schedules = conflicting_schedules.filter(
            Q(week_type=EvenOddBoth.BOTH) |
            Q(week_type=EvenOddBoth.EVEN) |
            Q(week_type=EvenOddBoth.ODD)
        )
    else:
        conflicting_schedules = conflicting_schedules.filter(
            Q(week_type=schedule_instance.week_type) |
            Q(week_type=EvenOddBoth.BOTH)
        )
    
    if conflicting_schedules.exists():
        conflict = conflicting_schedules.first()
        raise ValidationError(
            _(f'Конфликт расписания: аудитория "{audience.title}" уже занята '
              f'предметом "{conflict.subject.title}" в {schedule_instance.week_day.title} '
              f'на {schedule_instance.time_slot.number}-й паре ({schedule_instance.week_type})')
        )


def validate_teacher_schedule_conflict(schedule_instance):
    """
    Проверяет, что преподаватель не ведет несколько предметов одновременно.
    
    Args:
        schedule_instance: экземпляр модели SubjectSchedule
        
    Raises:
        ValidationError: если преподаватель уже занят
    """
    from .models import SubjectSchedule
    
    if not schedule_instance.pk:
        return
    
    teachers = schedule_instance.teachers.all()
    
    for teacher in teachers:
        # Ищем другие предметы этого преподавателя в это же время
        conflicting_schedules = SubjectSchedule.objects.filter(
            teachers=teacher,
            week_day=schedule_instance.week_day,
            time_slot=schedule_instance.time_slot,
        ).exclude(pk=schedule_instance.pk)
        
        # Фильтрация по типу недели
        if schedule_instance.week_type == EvenOddBoth.BOTH:
            conflicting_schedules = conflicting_schedules.filter(
                Q(week_type=EvenOddBoth.BOTH) |
                Q(week_type=EvenOddBoth.EVEN) |
                Q(week_type=EvenOddBoth.ODD)
            )
        else:
            conflicting_schedules = conflicting_schedules.filter(
                Q(week_type=schedule_instance.week_type) |
                Q(week_type=EvenOddBoth.BOTH)
            )
        
        if conflicting_schedules.exists():
            conflict = conflicting_schedules.first()
            teacher_name = f"{teacher.last_name} {teacher.first_name}" if teacher.last_name else teacher.username
            raise ValidationError(
                _(f'Конфликт расписания: преподаватель "{teacher_name}" уже ведет '
                  f'предмет "{conflict.subject.title}" в {schedule_instance.week_day.title} '
                  f'на {schedule_instance.time_slot.number}-й паре ({schedule_instance.week_type})')
            )


def check_schedule_conflicts(schedule_instance):
    """
    Проверяет все типы конфликтов расписания.
    
    Args:
        schedule_instance: экземпляр модели SubjectSchedule
        
    Raises:
        ValidationError: если найдены конфликты
    """
    validate_group_schedule_conflict(schedule_instance)
    validate_audience_schedule_conflict(schedule_instance)
    validate_teacher_schedule_conflict(schedule_instance)


def get_available_time_slots(group=None, teacher=None, audience=None, week_day=None, week_type=EvenOddBoth.BOTH):
    """
    Возвращает список доступных временных слотов для указанных параметров.
    
    Args:
        group: учебная группа (StudyGroups)
        teacher: преподаватель (User)
        audience: аудитория (Audiences)
        week_day: день недели (Day)
        week_type: тип недели ('EVEN', 'ODD', 'BOTH')
        
    Returns:
        QuerySet[TimeSlot]: доступные временные слоты
    """
    from .models import TimeSlot, SubjectSchedule
    
    # Получаем все возможные временные слоты
    all_slots = TimeSlot.objects.all()
    
    # Если указан день недели, фильтруем по нему
    if week_day:
        # Слоты, занятые в этот день
        occupied_slot_ids = []
        
        if group:
            # Слоты, занятые у группы
            occupied = SubjectSchedule.objects.filter(
                subject__groups=group,
                week_day=week_day
            )
            if week_type != EvenOddBoth.BOTH:
                occupied = occupied.filter(
                    Q(week_type=week_type) | Q(week_type=EvenOddBoth.BOTH)
                )
            occupied_slot_ids.extend(occupied.values_list('time_slot_id', flat=True))
        
        if teacher:
            # Слоты, занятые у преподавателя
            occupied = SubjectSchedule.objects.filter(
                subject__teachers=teacher,
                week_day=week_day
            )
            if week_type != EvenOddBoth.BOTH:
                occupied = occupied.filter(
                    Q(week_type=week_type) | Q(week_type=EvenOddBoth.BOTH)
                )
            occupied_slot_ids.extend(occupied.values_list('time_slot_id', flat=True))
        
        if audience:
            # Слоты, занятые в аудитории
            occupied = SubjectSchedule.objects.filter(
                subject__audience=audience,
                week_day=week_day
            )
            if week_type != EvenOddBoth.BOTH:
                occupied = occupied.filter(
                    Q(week_type=week_type) | Q(week_type=EvenOddBoth.BOTH)
                )
            occupied_slot_ids.extend(occupied.values_list('time_slot_id', flat=True))
        
        # Возвращаем свободные слоты
        available = all_slots.exclude(id__in=occupied_slot_ids)
        return available.distinct()
    
    return all_slots
