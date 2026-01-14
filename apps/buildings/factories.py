import factory
from factory.django import DjangoModelFactory
from faker import Faker

from .models import Buildings, AudiencesTypes, Audiences

fake = Faker('ru_RU')


class BuildingsFactory(DjangoModelFactory):
    """Фабрика для создания тестовых зданий"""
    
    class Meta:
        model = Buildings
    
    title = factory.Faker('company', locale='ru_RU')
    country = 'KG'
    region = factory.Faker('region', locale='ru_RU')
    city = factory.Faker('city', locale='ru_RU')
    street = factory.Faker('street_name', locale='ru_RU')
    house_number = factory.Faker('building_number', locale='ru_RU')


class AudiencesTypesFactory(DjangoModelFactory):
    """Фабрика для создания типов аудиторий"""
    
    class Meta:
        model = AudiencesTypes
    
    title = factory.Iterator(['Лекционная', 'Практическая', 'Лабораторная', 'Компьютерный класс'])


class AudiencesFactory(DjangoModelFactory):
    """Фабрика для создания аудиторий"""
    
    class Meta:
        model = Audiences
    
    auditorium_number = factory.Sequence(lambda n: 100 + n)
    auditorium_type = factory.SubFactory(AudiencesTypesFactory)
    floor_number = factory.Faker('random_int', min=1, max=5)
    building = factory.SubFactory(BuildingsFactory)
