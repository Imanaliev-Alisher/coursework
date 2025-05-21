from enumfields import Enum
from django.utils.translation import gettext as _


class WeekDays(Enum):
    MONDAY: str = 'Понедельник'
    TUESDAY: str = 'Вторник'
    WEDNESDAY: str = 'Среда'
    THURSDAY: str = 'Четверг'
    FRIDAY: str = 'Пятница'
    SATURDAY: str = 'Суббота'
    SUNDAY: str = 'Воскресенье'


class EvenOddBoth(Enum):
    EVEN: str = 'Четные'
    ODD: str = 'Нечетные'
    BOTH: str = 'Всегда'
