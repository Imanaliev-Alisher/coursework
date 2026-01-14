import factory
from factory.django import DjangoModelFactory
from faker import Faker

from .models import StudyGroups
from apps.users.factories import StudentFactory

fake = Faker('ru_RU')


class StudyGroupFactory(DjangoModelFactory):
    """Фабрика для создания учебных групп"""
    
    class Meta:
        model = StudyGroups
    
    title = factory.Sequence(lambda n: f'ГР-{2020 + n % 5}-{n:02d}')
    description = factory.Faker('text', max_nb_chars=200, locale='ru_RU')
    faculty = factory.Iterator(['Информатики', 'Экономики', 'Юриспруденции', 'Медицины'])
    course = factory.Faker('random_int', min=1, max=4)
    is_active = True
    
    @factory.post_generation
    def students(self, create, extracted, **kwargs):
        """Добавление студентов в группу"""
        if not create:
            return
        
        if extracted:
            for student in extracted:
                self.students.add(student)
