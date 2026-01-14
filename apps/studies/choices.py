from django.db import models
from django.utils.translation import gettext as _


class EvenOddBoth(models.TextChoices):
    EVEN = "Четные", _("Четные")
    ODD = "Нечетные", _("Нечетные")
    BOTH = "Все", _("Все")
