import factory
from factory.django import DjangoModelFactory
from faker import Faker
from datetime import time, date, timedelta

from .models import TimeSlot, Day, SubjectsTypes, Schedule, Subjects, ScheduleOverride
from .choices import EvenOddBoth
from apps.buildings.factories import AudiencesFactory
from apps.groups.factories import StudyGroupFactory
from apps.users.factories import TeacherFactory

fake = Faker('ru_RU')


class TimeSlotFactory(DjangoModelFactory):
    """Фабрика для создания временных слотов"""
    
    class Meta:
        model = TimeSlot
        django_get_or_create = ('number',)
    
    number = factory.Sequence(lambda n: (n % 6) + 1)  # 1-6 пары
    start_time = factory.LazyAttribute(lambda obj: time(8 + (obj.number - 1) * 2, 0))
    end_time = factory.LazyAttribute(lambda obj: time(8 + (obj.number - 1) * 2 + 1, 30))


class DayFactory(DjangoModelFactory):
    """Фабрика для создания дней недели"""
    
    class Meta:
        model = Day
        django_get_or_create = ('title',)
    
    title = factory.Iterator(['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота'])


class SubjectsTypesFactory(DjangoModelFactory):
    """Фабрика для создания типов предметов"""
    
    class Meta:
        model = SubjectsTypes
        django_get_or_create = ('title',)
    
    title = factory.Iterator(['Лекция', 'Практика', 'Лабораторная', 'Семинар'])


class ScheduleFactory(DjangoModelFactory):
    """Фабрика для создания расписания"""
    
    class Meta:
        model = Schedule
        django_get_or_create = ('week_day', 'time_slot', 'week_type')
    
    week_day = factory.SubFactory(DayFactory)
    time_slot = factory.SubFactory(TimeSlotFactory)
    week_type = EvenOddBoth.BOTH


class SubjectsFactory(DjangoModelFactory):
    """Фабрика для создания предметов"""
    
    class Meta:
        model = Subjects
    
    title = factory.Iterator([
        'Математика',
        'Программирование',
        'Базы данных',
        'Алгоритмы',
        'Операционные системы',
        'Сети'
    ])
    audience = factory.SubFactory(AudiencesFactory)
    subject_type = factory.SubFactory(SubjectsTypesFactory)
    
    @factory.post_generation
    def schedule(self, create, extracted, **kwargs):
        """Добавление расписаний"""
        if not create:
            return
        
        if extracted:
            for sched in extracted:
                self.schedule.add(sched)
        else:
            # По умолчанию добавляем одно расписание
            schedule = ScheduleFactory()
            self.schedule.add(schedule)
    
    @factory.post_generation
    def teachers(self, create, extracted, **kwargs):
        """Добавление преподавателей"""
        if not create:
            return
        
        if extracted:
            for teacher in extracted:
                self.teachers.add(teacher)
        else:
            teacher = TeacherFactory()
            self.teachers.add(teacher)
    
    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        """Добавление групп"""
        if not create:
            return
        
        if extracted:
            for group in extracted:
                self.groups.add(group)
        else:
            group = StudyGroupFactory()
            self.groups.add(group)


class ScheduleOverrideFactory(DjangoModelFactory):
    """Фабрика для переопределений расписания"""
    
    class Meta:
        model = ScheduleOverride
    
    subject = factory.SubFactory(SubjectsFactory)
    date = factory.LazyFunction(lambda: date.today() + timedelta(days=7))
    time_slot = factory.SubFactory(TimeSlotFactory)
    audience = factory.SubFactory(AudiencesFactory)
    is_cancelled = False
    notes = factory.Faker('sentence', locale='ru_RU')
