from apps.buildings.models import Audiences
from apps.groups.models import StudyGroups

from enumfields import EnumField
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .enums import WeekDays, EvenOddBoth


class Teachers(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('Пользователь'),
        help_text=_('Выберите пользователя который должен быть преподавателем')
    )
    position = models.CharField(
        max_length=63,
        blank=True,
        verbose_name=_('Должность'),
        help_text=_('Введите должность преподавателя')
    )

    class Meta:
        verbose_name = _('Преподаватель')
        verbose_name_plural = _('Преподаватели')

    def __str__(self):
        fullname = self.user.get_full_name()
        return fullname


class Students(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('Пользователь'),
        help_text=_('Выберите пользователя который должен быть студентом')
    )
    groups = models.ForeignKey(
        StudyGroups,
        on_delete=models.PROTECT,
        related_name='students',
        verbose_name=_('Учебная группа'),
        help_text=_('Выберите в какой учебной группе должен числиться этот студент.')
    )

    class Meta:
        verbose_name = _('Студент')
        verbose_name_plural = _('Студенты')

    def __str__(self):
        fullname = self.user.get_full_name()
        return fullname


class SubjectsTypes(models.Model):
    title = models.CharField(
        max_length=127,
        verbose_name=_('Наименование'),
        help_text=_('Введите наименование типа')
    )

    class Meta:
        verbose_name = _('Тип предмета')
        verbose_name_plural = _('Типы предметов')

    def __str__(self):
        return self.title


class Schedule(models.Model):
    week_day = EnumField(
        WeekDays, 
        max_length=31,
        verbose_name=_('День недели'),
        help_text=_('Выберите день недели')
    )
    time = models.TimeField(
        verbose_name=_('Время'),
        help_text=_('Выберите время')
    )
    week_type = EnumField(
        EvenOddBoth,
        max_length=31,
        verbose_name=_('Тип недели'),
        help_text=_('Выберите тип недели')
    )

    class Meta:
        verbose_name = _('Расписание')
        verbose_name_plural = _('Расписании')

    def __str__(self):
        return f"{self.week_day}: {self.week_type}: {self.time}"


class Subjects(models.Model):
    title = models.CharField(
        max_length=255,
        verbose_name=_("Название предмета"),
        help_text=_('Введите назвние предмета')
    )
    schedule = models.ManyToManyField(
        Schedule,
        verbose_name=_('Расписание'),
        help_text=_('Выберите подходящие расписание')
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
        Teachers,
        verbose_name=_('Преподователи'),
        help_text=_('Выберите преподавателей предмета')
    )
    groups = models.ManyToManyField(
        StudyGroups,
        verbose_name=_('Учебная группа'),
        help_text=_('Выберите учебные группы')
    )

    class Meta:
        verbose_name = _('Предмет')
        verbose_name_plural = _('Предметы')

    def __str__(self):
        return f"{self.title} ({self.subject_type.__str__()})"
