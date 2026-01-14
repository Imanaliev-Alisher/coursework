from django.db import models
from django.utils.translation import gettext_lazy as _


class GenderChoices(models.TextChoices):
    MALE = "M", _("Male")
    FEMALE = "F", _("Female")
    NOT_SPECIFIED = "N", _("Not specified")


class RoleChoices(models.TextChoices):
    STUDENT = "STUDENT", _("Student")
    TEACHER = "TEACHER", _("Teacher")
    STAFF = "STAFF", _("Staff")
