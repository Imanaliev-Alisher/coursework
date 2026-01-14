"""
Фабрики для создания тестовых данных пользователей
"""
import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from faker import Faker

fake = Faker('ru_RU')
User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Фабрика для создания пользователей"""
    
    class Meta:
        model = User
        django_get_or_create = ('username',)
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@test.com')
    first_name = factory.LazyFunction(lambda: fake.first_name())
    last_name = factory.LazyFunction(lambda: fake.last_name())
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')
    is_active = True
    role = 'STUDENT'
    gender = 'N'


class StudentFactory(UserFactory):
    """Фабрика для создания студентов"""
    role = 'STUDENT'


class TeacherFactory(UserFactory):
    """Фабрика для создания преподавателей"""
    role = 'TEACHER'
    department = factory.LazyFunction(lambda: fake.company())
    phone = factory.LazyFunction(lambda: fake.phone_number())
    office = factory.LazyFunction(lambda: f'{fake.random_int(100, 999)}{fake.random_element(["А", "Б", "В"])}')


class StaffFactory(UserFactory):
    """Фабрика для создания сотрудников"""
    role = 'STAFF'
    is_staff = True


class AdminFactory(UserFactory):
    """Фабрика для создания администраторов"""
    role = 'STAFF'
    is_staff = True
    is_superuser = True
