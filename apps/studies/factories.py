import factory
from factory.django import DjangoModelFactory
from faker import Faker
from datetime import time, date, timedelta

from .models import TimeSlot, Day, SubjectsTypes, SubjectSchedule, Subjects
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


class SubjectScheduleFactory(DjangoModelFactory):
    """Фабрика для создания расписания предмета"""
    
    class Meta:
        model = SubjectSchedule
        django_get_or_create = ('subject', 'week_day', 'time_slot', 'week_type')
    
    subject = factory.SubFactory('apps.studies.factories.SubjectsFactory')
    week_day = factory.SubFactory(DayFactory)
    time_slot = factory.SubFactory(TimeSlotFactory)
    week_type = EvenOddBoth.BOTH
    
    @factory.post_generation
    def teachers(self, create, extracted, **kwargs):
        """Добавление преподавателей к расписанию"""
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
        """Добавление групп к расписанию"""
        if not create:
            return
        
        if extracted:
            for group in extracted:
                self.groups.add(group)
        else:
            group = StudyGroupFactory()
            self.groups.add(group)


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
