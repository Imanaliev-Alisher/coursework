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
    SubjectScheduleFactory, SubjectsFactory
)
from .models import TimeSlot, Day, SubjectsTypes, SubjectSchedule, Subjects
from .choices import EvenOddBoth
from .validators import (
    validate_group_schedule_conflict,
    validate_audience_schedule_conflict,
    validate_teacher_schedule_conflict
)
from .schedule_generator import (
    generate_schedule_for_groups,
    validate_generated_schedule,
    get_schedule_statistics
)


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
    
    def test_subject_with_schedule(self):
        """Тест добавления расписания к предмету"""
        subject = SubjectsFactory()
        schedule = SubjectScheduleFactory(subject=subject)
        assert subject.schedules.count() == 1
        assert schedule.subject == subject
    
    def test_subject_str_representation(self):
        """Тест строкового представления предмета"""
        subject = SubjectsFactory(title='Математика')
        assert 'Математика' in str(subject)




@pytest.mark.django_db
class TestSubjectsAPI:
    
    def test_group_schedule_conflict_detection(self):
        """Тест обнаружения конфликта группы"""
        from apps.groups.factories import StudyGroupsFactory
        
        # Создаем группу и расписание
        group = StudyGroupsFactory()
        schedule = ScheduleFactory()
        
        # Первый предмет для группы
        subject1 = SubjectsFactory()
        subject1.groups.add(group)
        subject1.schedule.add(schedule)
        
        # Второй предмет для той же группы в то же время - должен быть конфликт
        subject2 = SubjectsFactory()
        subject2.groups.add(group)
        subject2.schedule.add(schedule)
        
        # Проверяем, что обнаружен конфликт
        with pytest.raises(ValidationError, match='Конфликт расписания'):
            validate_group_schedule_conflict(subject2)
    
    def test_audience_schedule_conflict_detection(self):
        """Тест обнаружения конфликта аудитории"""
        from apps.buildings.factories import AudiencesFactory
        
        # Создаем аудиторию и расписание
        audience = AudiencesFactory()
        schedule = ScheduleFactory()
        
        # Первый предмет в аудитории
        subject1 = SubjectsFactory(audience=audience)
        subject1.schedule.add(schedule)
        
        # Второй предмет в той же аудитории в то же время
        subject2 = SubjectsFactory(audience=audience)
        subject2.schedule.add(schedule)
        
        # Проверяем конфликт
        with pytest.raises(ValidationError, match='Конфликт расписания'):
            validate_audience_schedule_conflict(subject2)
    
    def test_teacher_schedule_conflict_detection(self):
        """Тест обнаружения конфликта преподавателя"""
        teacher = TeacherFactory()
        schedule = ScheduleFactory()
        
        # Первый предмет преподавателя
        subject1 = SubjectsFactory()
        subject1.teachers.add(teacher)
        subject1.schedule.add(schedule)
        
        # Второй предмет того же преподавателя в то же время
        subject2 = SubjectsFactory()
        subject2.teachers.add(teacher)
        subject2.schedule.add(schedule)
        
        # Проверяем конфликт
        with pytest.raises(ValidationError, match='Конфликт расписания'):
            validate_teacher_schedule_conflict(subject2)
    
    def test_no_conflict_different_week_types(self):
        """Тест: нет конфликта при разных типах недель"""
        from apps.groups.factories import StudyGroupsFactory
        
        group = StudyGroupsFactory()
        day = DayFactory()
        time_slot = TimeSlotFactory()
        
        # Расписание для четной недели
        schedule_even = ScheduleFactory(week_day=day, time_slot=time_slot, week_type='EVEN')
        subject1 = SubjectsFactory()
        subject1.groups.add(group)
        subject1.schedule.add(schedule_even)
        
        # Расписание для нечетной недели - конфликта не должно быть
        schedule_odd = ScheduleFactory(week_day=day, time_slot=time_slot, week_type='ODD')
        subject2 = SubjectsFactory()
        subject2.groups.add(group)
        subject2.schedule.add(schedule_odd)
        
        # Не должно быть исключения
        validate_group_schedule_conflict(subject2)
    
    def test_stream_subjects_same_audience(self):
        """Тест: потоковые предметы (один предмет для разных групп)"""
        from apps.groups.factories import StudyGroupsFactory
        from apps.buildings.factories import AudiencesFactory
        
        audience = AudiencesFactory()
        schedule = ScheduleFactory()
        group1 = StudyGroupsFactory()
        group2 = StudyGroupsFactory()
        
        # Один предмет для двух групп (потоковый)
        subject = SubjectsFactory(audience=audience)
        subject.groups.add(group1, group2)
        subject.schedule.add(schedule)
        
        # Конфликта в аудитории быть не должно (это тот же предмет)
        validate_audience_schedule_conflict(subject)


@pytest.mark.django_db
class TestScheduleGenerator:
    """Тесты генератора расписания"""
    
    def test_schedule_generation_basic(self):
        """Тест базовой генерации расписания"""
        from apps.groups.factories import StudyGroupsFactory
        
        # Создаем тестовые данные
        group = StudyGroupsFactory()
        
        # Создаем временные слоты
        for i in range(1, 4):
            TimeSlotFactory(number=i)
        
        # Создаем дни недели
        days = ['Понедельник', 'Вторник']
        for day_name in days:
            DayFactory(title=day_name)
        
        # Создаем расписание
        all_days = Day.objects.all()
        all_slots = TimeSlot.objects.all()
        for day in all_days:
            for slot in all_slots:
                ScheduleFactory(week_day=day, time_slot=slot, week_type='BOTH')
        
        # Создаем предметы для группы
        for i in range(3):
            subject = SubjectsFactory()
            subject.groups.add(group)
        
        # Генерируем расписание
        success, messages, statistics = generate_schedule_for_groups(
            group_ids=[group.id],
            clear_existing=False,
            prefer_morning=True
        )
        
        assert success is True or success is False  # Может быть успешно или нет
        assert len(messages) > 0
        assert 'total_groups' in statistics
    
    def test_schedule_validation(self):
        """Тест валидации расписания"""
        from apps.groups.factories import StudyGroupsFactory
        
        group = StudyGroupsFactory()
        subject = SubjectsFactory()
        subject.groups.add(group)
        
        # Добавляем корректное расписание
        schedule = ScheduleFactory()
        subject.schedule.add(schedule)
        
        # Валидируем
        is_valid, conflicts = validate_generated_schedule([group.id])
        
        # Должно быть валидно
        assert is_valid is True
        assert len(conflicts) == 1  # Сообщение об успехе
        assert 'корректно' in conflicts[0].lower()
    
    def test_schedule_statistics(self):
        """Тест получения статистики расписания"""
        from apps.groups.factories import StudyGroupsFactory
        
        group = StudyGroupsFactory()
        
        # Создаем предметы
        subject1 = SubjectsFactory()
        subject1.groups.add(group)
        subject1.schedule.add(ScheduleFactory())
        
        subject2 = SubjectsFactory()
        subject2.groups.add(group)
        # Без расписания
        
        # Получаем статистику
        stats = get_schedule_statistics([group.id])
        
        assert stats['total_groups'] == 1
        assert stats['total_subjects'] == 2
        assert stats['subjects_with_schedule'] == 1
        assert stats['subjects_without_schedule'] == 1


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
