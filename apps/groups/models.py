from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class StudyGroups(models.Model):
    title = models.CharField(
        _('Наименование учебной группы'),
        max_length=50,
        help_text=_("Введите Наименование учебной группы")
    )
    description = models.TextField(
        _('Описание учебной группы'),
        help_text=_('Введите описание(дополнительную информацию) об учебной группе')
    )
    faculty = models.CharField(
        _('Факультет'),
        max_length=255,
        blank=True,
        help_text=_("Факультет, к которому относится группа")
    )
    course = models.PositiveSmallIntegerField(
        _('Курс'),
        null=True,
        blank=True,
        help_text=_("Курс обучения (1-6)")
    )
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='study_groups',
        verbose_name=_('Студенты'),
        help_text=_('Выберите студентов группы'),
        limit_choices_to={'role': 'STUDENT'}
    )
    is_active = models.BooleanField(
        _('Активна'),
        default=True,
        help_text=_('Действующая группа или нет')
    )

    class Meta:
        verbose_name = _('Учебная группа')
        verbose_name_plural = _('Учебные группы')

    def clean(self):
        if not self.title:
            raise ValidationError(
                _('Наименование учебной группы не может быть пустым.'),
                code='invalid_title'
            )
        return super().clean()

    def __str__(self):
        return self.title
