from django.db import models
from django.utils.translation import gettext_lazy as _


class StudyGroups(models.Model):
    title = models.CharField(
        max_length=50,
        verbose_name=_('Наименование учебной группы'),
        help_text=_("Введите Наименование учебной группы")
    )
    description = models.TextField(
        verbose_name=_('Описание учебной группы'),
        help_text=_('Введите описание(дополнительную информацию) об учебной группе')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активна'),
        help_text=_('Действующая группа или нет')
    )

    class Meta:
        verbose_name = _('Учебная группа')
        verbose_name_plural = _('Учебные группы')

    def __str__(self):
        return self.title
