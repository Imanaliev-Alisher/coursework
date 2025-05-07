from django.db import models
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField


class Buildings(models.Model):
    title = models.CharField(
        max_length=255,
        verbose_name=_('Строение(Корпус)'),
        help_text=_('Введите наименование строения(корпуса)')
    )
    country = CountryField(
        verbose_name=_('Страна'),
        help_text=_('Введите страну где находится строение(корпус)')
    )
    region = models.CharField(
        max_length=100,
        verbose_name=_('Регион'),
        blank=True,
        help_text=_('Введите регион где находится строение(корпус)')
    )
    city = models.CharField(
        max_length=100,
        verbose_name=_('Город'),
        help_text=_('Введите город где находится строение(корпус)')
    )
    street = models.CharField(
        max_length=255,
        verbose_name=_('Улица'),
        help_text=_('Введите улицу где находится строение(корпус)')
    )
    house_number = models.CharField(
        max_length=100,
        verbose_name=_('Номер строения'),
        help_text=_('Введите номер строения')
    )
    address = models.TextField(
        blank=True,
        verbose_name=_('Адрес строения'),
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
        max_length=63,
        verbose_name=_('Название'),
        help_text=_('Введите название типа')
    )

    class Meta:
        verbose_name = _('Тип аудитории')
        verbose_name_plural = _('Типы аудиторий')

    def __str__(self):
        return self.title


class Audiences(models.Model):
    title = models.CharField(
        max_length=63,
        verbose_name=_('Введите название аудитории'),
        blank=True,
        help_text=_('Название (если не указано — сформируется автоматически)')
    )
    auditorium_number = models.PositiveSmallIntegerField(
        verbose_name=_('Номер аудитории'),
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
        verbose_name=_('Этаж'),
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
