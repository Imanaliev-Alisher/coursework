from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class User(AbstractUser):

    REQUIRED_FIELDS = []

    objects = UserManager()
