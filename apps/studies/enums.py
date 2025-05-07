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

    class Labels:
        MONDAY = _('Понедельник')
        TUESDAY = _('Вторник')
        WEDNESDAY = _('Среда')
        THURSDAY = _('Четверг')
        FRIDAY = _('Пятница')
        SATURDAY = _('Суббота')
        SUNDAY = _('Воскресенье')


class EvenOddBoth(Enum):
    EVEN: str = 'Четные'
    ODD: str = 'Нечетные'
    BOTH: str = 'Всегда'

    class Labels:
        EVEN = _('Четные')
        ODD = _('Нечетные')
        BOTH = _('Всегда')
