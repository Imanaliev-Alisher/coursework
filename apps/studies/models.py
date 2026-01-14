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


class Schedule(models.Model):
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

    class Meta:
        verbose_name = _('Расписание')
        verbose_name_plural = _('Расписания')
        unique_together = ['week_day', 'time_slot', 'week_type']

    def __str__(self):
        return f"{self.week_day} - {self.time_slot} ({self.week_type})"


class Subjects(models.Model):
    title = models.CharField(
        _("Название предмета"),
        max_length=255,
        help_text=_('Введите название предмета')
    )
    schedule = models.ManyToManyField(
        Schedule,
        verbose_name=_('Расписание'),
        help_text=_('Выберите подходящее расписание')
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
    teachers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='teaching_subjects',
        verbose_name=_('Преподаватели'),
        help_text=_('Выберите преподавателей предмета'),
        limit_choices_to={'role': 'TEACHER'}
    )
    groups = models.ManyToManyField(
        StudyGroups,
        related_name='subjects',
        verbose_name=_('Учебные группы'),
        help_text=_('Выберите учебные группы')
    )

    class Meta:
        verbose_name = _('Предмет')
        verbose_name_plural = _('Предметы')

    def __str__(self):
        return f"{self.title} ({self.subject_type})"


class ScheduleOverride(models.Model):
    """
    Переопределение расписания для конкретной недели.
    Позволяет создавать динамическое расписание на определенный период.
    """
    subject = models.ForeignKey(
        Subjects,
        on_delete=models.CASCADE,
        related_name='schedule_overrides',
        verbose_name=_('Предмет'),
        help_text=_('Выберите предмет')
    )
    date = models.DateField(
        _('Дата'),
        help_text=_('Дата проведения занятия')
    )
    time_slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.PROTECT,
        verbose_name=_('Временной слот (пара)'),
        help_text=_('Выберите номер пары')
    )
    audience = models.ForeignKey(
        Audiences,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_('Аудитория (переопределение)'),
        help_text=_('Оставьте пустым, чтобы использовать аудиторию из основного расписания')
    )
    is_cancelled = models.BooleanField(
        _('Занятие отменено'),
        default=False,
        help_text=_('Отметьте, если занятие отменяется')
    )
    notes = models.TextField(
        _('Примечания'),
        blank=True,
        help_text=_('Дополнительная информация об изменении')
    )

    class Meta:
        verbose_name = _('Переопределение расписания')
        verbose_name_plural = _('Переопределения расписания')
        unique_together = ['subject', 'date', 'time_slot']
        ordering = ['date', 'time_slot__number']

    def __str__(self):
        status = _('Отменено') if self.is_cancelled else _('Перенесено')
        return f"{self.subject.title} - {self.date} ({status})"

