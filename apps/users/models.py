from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

from .choices import GenderChoices, RoleChoices
from .managers import UserManager


class User(AbstractUser):

    gender = models.CharField(
        _("Gender"),
        max_length=1,
        choices=GenderChoices.choices,
        default=GenderChoices.NOT_SPECIFIED,
    )

    role = models.CharField(
        _("Role"),
        max_length=10,
        choices=RoleChoices.choices,
        default=RoleChoices.STUDENT,
    )

    # Дополнительные поля для преподавателей
    department = models.CharField(
        _("Кафедра"),
        max_length=255,
        blank=True,
        help_text=_("Кафедра преподавателя")
    )

    phone = models.CharField(
        _("Телефон"),
        max_length=20,
        blank=True,
        help_text=_("Контактный телефон")
    )

    office = models.CharField(
        _("Кабинет"),
        max_length=50,
        blank=True,
        help_text=_("Номер кабинета преподавателя")
    )

    REQUIRED_FIELDS = ['email']

    objects = UserManager()
