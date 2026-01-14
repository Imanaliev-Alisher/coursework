import pytest
from datetime import time, date, timedelta
from django.urls import reverse
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.factories import UserFactory, AdminFactory, TeacherFactory
from apps.users.choices import RoleChoices
from .factories import (
    TimeSlotFactory, DayFactory, SubjectsTypesFactory,
    ScheduleFactory, SubjectsFactory, ScheduleOverrideFactory
)
from .models import TimeSlot, Day, SubjectsTypes, Schedule, Subjects, ScheduleOverride
from .choices import EvenOddBoth


@pytest.mark.django_db
class TestTimeSlotModel:
    """Тесты модели TimeSlot"""
    
    def test_create_time_slot(self):
        """Тест создания временного слота"""
        time_slot = TimeSlotFactory(number=1, start_time=time(8, 0), end_time=time(9, 30))
        assert time_slot.id is not None
        assert time_slot.number == 1
    
    def test_time_slot_str_representation(self):
        """Тест строкового представления слота"""
        time_slot = TimeSlotFactory(number=2, start_time=time(10, 0), end_time=time(11, 30))
        assert '2-я пара' in str(time_slot)
        assert '10:00' in str(time_slot)
    
    def test_time_slot_validation_end_before_start(self):
        """Тест валидации: конец не может быть раньше начала"""
        time_slot = TimeSlot(number=1, start_time=time(10, 0), end_time=time(8, 0))
        with pytest.raises(ValidationError):
            time_slot.clean()
    
    def test_time_slot_unique_number(self):
        """Тест уникальности номера слота"""
        TimeSlot.objects.create(number=1, start_time=time(8, 0), end_time=time(9, 30))
        # Второй слот с тем же номером должен вызвать ошибку
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            TimeSlot.objects.create(number=1, start_time=time(10, 0), end_time=time(11, 30))


@pytest.mark.django_db
class TestDayModel:
    """Тесты модели Day"""
    
    def test_create_day(self):
        """Тест создания дня недели"""
        day = DayFactory(title='Понедельник')
        assert day.id is not None
        assert day.title == 'Понедельник'
    
    def test_day_str_representation(self):
        """Тест строкового представления дня"""
        day = DayFactory(title='Вторник')
        assert str(day) == 'Вторник'


@pytest.mark.django_db
class TestSubjectsTypesModel:
    """Тесты модели SubjectsTypes"""
    
    def test_create_subject_type(self):
        """Тест создания типа предмета"""
        subj_type = SubjectsTypesFactory(title='Лекция')
        assert subj_type.id is not None
        assert subj_type.title == 'Лекция'
    
    def test_subject_type_str_representation(self):
        """Тест строкового представления типа"""
        subj_type = SubjectsTypesFactory(title='Практика')
        assert str(subj_type) == 'Практика'


@pytest.mark.django_db
class TestScheduleModel:
    """Тесты модели Schedule"""
    
    def test_create_schedule(self):
        """Тест создания расписания"""
        schedule = ScheduleFactory()
        assert schedule.id is not None
        assert schedule.week_day is not None
        assert schedule.time_slot is not None
    
    def test_schedule_str_representation(self):
        """Тест строкового представления расписания"""
        day = DayFactory(title='Среда')
        time_slot = TimeSlotFactory(number=3)
        schedule = ScheduleFactory(week_day=day, time_slot=time_slot, week_type=EvenOddBoth.EVEN)
        assert 'Среда' in str(schedule)
    
    def test_schedule_unique_together(self):
        """Тест уникальности комбинации день+слот+тип недели"""
        day = DayFactory()
        time_slot = TimeSlotFactory()
        Schedule.objects.create(week_day=day, time_slot=time_slot, week_type=EvenOddBoth.BOTH)
        
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            Schedule.objects.create(week_day=day, time_slot=time_slot, week_type=EvenOddBoth.BOTH)


@pytest.mark.django_db
class TestSubjectsModel:
    """Тесты модели Subjects"""
    
    def test_create_subject(self):
        """Тест создания предмета"""
        subject = SubjectsFactory()
        assert subject.id is not None
        assert subject.title is not None
        assert subject.audience is not None
    
    def test_subject_with_teachers(self):
        """Тест добавления преподавателей к предмету"""
        teachers = TeacherFactory.create_batch(2)
        subject = SubjectsFactory(teachers=teachers)
        assert subject.teachers.count() == 2
    
    def test_subject_str_representation(self):
        """Тест строкового представления предмета"""
        subject = SubjectsFactory(title='Математика')
        assert 'Математика' in str(subject)


@pytest.mark.django_db
class TestScheduleOverrideModel:
    """Тесты модели ScheduleOverride"""
    
    def test_create_schedule_override(self):
        """Тест создания переопределения расписания"""
        override = ScheduleOverrideFactory()
        assert override.id is not None
        assert override.subject is not None
        assert override.date is not None
    
    def test_schedule_override_cancelled(self):
        """Тест отмененного занятия"""
        override = ScheduleOverrideFactory(is_cancelled=True)
        assert override.is_cancelled is True
        assert 'Отменено' in str(override)


@pytest.mark.django_db
class TestSubjectsAPI:
    """Тесты API для предметов"""
    
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    @pytest.fixture
    def admin_user(self):
        return AdminFactory()
    
    @pytest.fixture
    def regular_user(self):
        return UserFactory(role=RoleChoices.STUDENT)
    
    @pytest.fixture
    def auth_token(self, admin_user):
        refresh = RefreshToken.for_user(admin_user)
        return str(refresh.access_token)
    
    def test_list_subjects(self, api_client, auth_token):
        """Тест получения списка предметов"""
        SubjectsFactory.create_batch(3)
        url = reverse('studies:subject-list')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 3
    
    def test_get_subject_detail(self, api_client, auth_token):
        """Тест получения детальной информации о предмете"""
        subject = SubjectsFactory()
        url = reverse('studies:subject-detail', kwargs={'pk': subject.pk})
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == subject.title
    
    def test_create_subject_regular_user(self, api_client, regular_user):
        """Тест попытки создания предмета обычным пользователем"""
        refresh = RefreshToken.for_user(regular_user)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        url = reverse('studies:subject-list')
        data = {'title': 'Новый предмет'}
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestScheduleAPI:
    """Тесты API для расписания"""
    
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    @pytest.fixture
    def admin_user(self):
        return AdminFactory()
    
    @pytest.fixture
    def auth_token(self, admin_user):
        refresh = RefreshToken.for_user(admin_user)
        return str(refresh.access_token)
    
    def test_list_schedules(self, api_client, auth_token):
        """Тест получения списка расписаний"""
        ScheduleFactory.create_batch(3)
        url = reverse('studies:schedule-list')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestTimeSlotAPI:
    """Тесты API для временных слотов"""
    
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    @pytest.fixture
    def admin_user(self):
        return AdminFactory()
    
    @pytest.fixture
    def auth_token(self, admin_user):
        refresh = RefreshToken.for_user(admin_user)
        return str(refresh.access_token)
    
    def test_list_time_slots(self, api_client, auth_token):
        """Тест получения списка временных слотов"""
        TimeSlotFactory.create_batch(5)
        url = reverse('studies:timeslot-list')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 5


@pytest.mark.django_db
class TestScheduleOverrideAPI:
    """Тесты API для переопределений расписания"""
    
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    @pytest.fixture
    def admin_user(self):
        return AdminFactory()
    
    @pytest.fixture
    def auth_token(self, admin_user):
        refresh = RefreshToken.for_user(admin_user)
        return str(refresh.access_token)
    
    def test_list_schedule_overrides(self, api_client, auth_token):
        """Тест получения списка переопределений"""
        ScheduleOverrideFactory.create_batch(2)
        url = reverse('studies:schedule-override-list')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
    
    def test_create_schedule_override_cancelled(self, api_client, auth_token):
        """Тест создания отмены занятия"""
        subject = SubjectsFactory()
        time_slot = TimeSlotFactory()
        
        url = reverse('studies:schedule-override-list')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        data = {
            'subject': subject.id,
            'date': (date.today() + timedelta(days=7)).isoformat(),
            'time_slot': time_slot.id,
            'is_cancelled': True,
            'notes': 'Занятие отменено'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert ScheduleOverride.objects.filter(is_cancelled=True).exists()
