from apps.buildings.models import Audiences
from apps.groups.models import StudyGroups

from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .choices import EvenOddBoth


class TimeSlot(models.Model):
    """Временной слот (пара) - например, 1-я пара: 8:00-9:30"""
    number = models.PositiveSmallIntegerField(
        _('Номер пары'),
        unique=True,
        help_text=_('Введите номер пары (1, 2, 3...)')
    )
    start_time = models.TimeField(
        _('Время начала'),
        help_text=_('Введите время начала пары')
    )
    end_time = models.TimeField(
        _('Время окончания'),
        help_text=_('Введите время окончания пары')
    )

    class Meta:
        verbose_name = _('Временной слот (пара)')
        verbose_name_plural = _('Временные слоты (пары)')
        ordering = ['number']

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError(
                _('Время начала должно быть меньше времени окончания')
            )

    def __str__(self):
        return f"{self.number}-я пара ({self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')})"


class Day(models.Model):
    title = models.CharField(
        _('Наименование'),
        max_length=31,
        help_text=_('Введите наименование дня недели')
    )

    class Meta:
        verbose_name = _('День недели')
        verbose_name_plural = _('Дни недели')

    def __str__(self):
        return self.title


class SubjectsTypes(models.Model):
    title = models.CharField(
        _('Наименование'),
        max_length=127,
        help_text=_('Введите наименование типа')
    )

    class Meta:
        verbose_name = _('Тип предмета')
        verbose_name_plural = _('Типы предметов')

    def __str__(self):
        return self.title


class Subjects(models.Model):
    title = models.CharField(
        _("Название предмета"),
        max_length=255,
        help_text=_('Введите название предмета')
    )
    audience = models.ForeignKey(
        Audiences,
        on_delete=models.PROTECT,
        related_name='subjects',
        verbose_name=_('Аудитория'),
        help_text=_('Выберите аудиторию')
    )
    subject_type = models.ForeignKey(
        SubjectsTypes,
        on_delete=models.PROTECT,
        related_name="subjects",
        verbose_name=_('Тип предмета'),
        help_text=_('Выберите тип предмета')
    )

    class Meta:
        verbose_name = _('Предмет')
        verbose_name_plural = _('Предметы')

    def __str__(self):
        return f"{self.title} ({self.subject_type})"


class SubjectSchedule(models.Model):
    """
    Расписание предмета - связь между предметом и временным слотом.
    Заменяет сложную структуру с предварительно созданными комбинациями.
    """
    subject = models.ForeignKey(
        Subjects,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name=_('Предмет'),
        help_text=_('Выберите предмет')
    )
    week_day = models.ForeignKey(
        Day,
        on_delete=models.PROTECT,
        verbose_name=_('День недели'),
        help_text=_('Выберите день недели')
    )
    time_slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.PROTECT,
        verbose_name=_('Временной слот (пара)'),
        help_text=_('Выберите номер пары')
    )
    week_type = models.CharField(
        _('Тип недели'),
        choices=EvenOddBoth.choices,
        default=EvenOddBoth.BOTH,
        max_length=31,
        help_text=_('Выберите тип недели')
    )
    teachers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='teaching_schedules',
        verbose_name=_('Преподаватели'),
        help_text=_('Выберите преподавателей для этого занятия'),
        limit_choices_to={'role': 'TEACHER'}
    )
    groups = models.ManyToManyField(
        StudyGroups,
        related_name='schedules',
        verbose_name=_('Учебные группы'),
        help_text=_('Выберите учебные группы для этого занятия')
    )

    class Meta:
        verbose_name = _('Расписание предмета')
        verbose_name_plural = _('Расписания предметов')
        unique_together = ['subject', 'week_day', 'time_slot', 'week_type']
        ordering = ['week_day', 'time_slot__number']

    def clean(self):
        """Валидация на конфликты расписания"""
        super().clean()
        
        # Импортируем здесь, чтобы избежать циклических импортов
        from .validators import check_schedule_conflicts
        
        # Проверяем только если объект уже сохранен (есть pk)
        if self.pk:
            check_schedule_conflicts(self)

    def save(self, *args, **kwargs):
        """Переопределяем save для валидации перед сохранением"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.subject.title} - {self.week_day} {self.time_slot} ({self.week_type})"

