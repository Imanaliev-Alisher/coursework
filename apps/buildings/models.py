from django.db import models
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField


class Buildings(models.Model):
    title = models.CharField(
        _('Строение(Корпус)'),
        max_length=255,
        help_text=_('Введите наименование строения(корпуса)')
    )
    country = CountryField(
        _('Страна'),
        help_text=_('Введите страну где находится строение(корпус)')
    )
    region = models.CharField(
        _('Регион'),
        max_length=100,
        blank=True,
        help_text=_('Введите регион где находится строение(корпус)')
    )
    city = models.CharField(
        _('Город'),
        max_length=100,
        help_text=_('Введите город где находится строение(корпус)')
    )
    street = models.CharField(
        _('Улица'),
        max_length=255,
        help_text=_('Введите улицу где находится строение(корпус)')
    )
    house_number = models.CharField(
        _('Номер строения'),
        max_length=100,
        help_text=_('Введите номер строения')
    )
    address = models.TextField(
        _('Адрес строения'),
        blank=True,
        help_text=_('Введите адрес строения')
    )

    class Meta:
        verbose_name = _('Строение(Корпус)')
        verbose_name_plural = _('Строении(Корпусы)')

    def save(self, *args, **kwargs):
        if not self.address:
            region = f"{self.region}/" if self.region else ""
            self.address = f"{self.country}/{region}/{self.city}/{self.street}/{self.house_number}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    

class AudiencesTypes(models.Model):
    title = models.CharField(
        _('Название'),
        max_length=63,
        help_text=_('Введите название типа')
    )

    class Meta:
        verbose_name = _('Тип аудитории')
        verbose_name_plural = _('Типы аудиторий')

    def __str__(self):
        return self.title


class Audiences(models.Model):
    title = models.CharField(
        _('Введите название аудитории'),
        max_length=63,
        blank=True,
        help_text=_('Название (если не указано — сформируется автоматически)')
    )
    auditorium_number = models.PositiveSmallIntegerField(
        _('Номер аудитории'),
        help_text=_('Введите номер аудитории')
    )
    auditorium_type = models.ForeignKey(
        AudiencesTypes,
        max_length=50,
        on_delete=models.PROTECT,
        related_name="audience",
        verbose_name=_('Тип аудитории'),
        help_text=_('Выберите тип аудитории')
    )
    floor_number = models.PositiveSmallIntegerField(
        _('Этаж'),
        help_text=_('Введите этаж на котором находиться аудитория')
    )
    building = models.ForeignKey(
        Buildings,
        on_delete=models.PROTECT,
        related_name='audiences',
        verbose_name=_('Строение(Корпус)'),
        help_text=_('Выберите строение(корпус) в котором находится аудитория')
    )

    class Meta:
        verbose_name = _('Аудитория')
        verbose_name_plural = _('Аудитории')

    def save(self, *args, **kwargs):
        if not self.title:
            self.title = f"{self.auditorium_type} {self.auditorium_number}"
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
