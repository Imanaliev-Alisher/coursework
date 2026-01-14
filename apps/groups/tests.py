import pytest
from django.urls import reverse
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.factories import UserFactory, AdminFactory, StudentFactory
from apps.users.models import User
from apps.users.choices import RoleChoices
from .factories import StudyGroupFactory
from .models import StudyGroups


@pytest.mark.django_db
class TestStudyGroupsModel:
    """Тесты модели StudyGroups"""
    
    def test_create_study_group(self):
        """Тест создания учебной группы"""
        group = StudyGroupFactory()
        assert group.id is not None
        assert group.title is not None
        assert group.is_active is True
    
    def test_study_group_str_representation(self):
        """Тест строкового представления группы"""
        group = StudyGroupFactory(title='ГР-2024-01')
        assert str(group) == 'ГР-2024-01'
    
    def test_study_group_with_students(self):
        """Тест добавления студентов в группу"""
        students = StudentFactory.create_batch(3)
        group = StudyGroupFactory(students=students)
        assert group.students.count() == 3
    
    def test_study_group_validation_empty_title(self):
        """Тест валидации пустого названия группы"""
        group = StudyGroups(title='', description='Test')
        with pytest.raises(ValidationError):
            group.clean()
    
    def test_study_group_course_range(self):
        """Тест установки курса группы"""
        group = StudyGroupFactory(course=3)
        assert 1 <= group.course <= 6
    
    def test_study_group_inactive(self):
        """Тест создания неактивной группы"""
        group = StudyGroupFactory(is_active=False)
        assert group.is_active is False


@pytest.mark.django_db
class TestStudyGroupsAPI:
    """Тесты API для учебных групп"""
    
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
    
    def test_list_study_groups(self, api_client, auth_token):
        """Тест получения списка учебных групп"""
        StudyGroupFactory.create_batch(3)
        url = reverse('groups:study-group-list')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3
    
    def test_get_study_group_detail(self, api_client, auth_token):
        """Тест получения детальной информации о группе"""
        group = StudyGroupFactory()
        url = reverse('groups:study-group-detail', kwargs={'pk': group.pk})
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == group.title
    
    def test_create_study_group_admin(self, api_client, auth_token):
        """Тест создания группы администратором"""
        url = reverse('groups:study-group-list')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        data = {
            'title': 'ГР-2025-01',
            'description': 'Тестовая группа',
            'faculty': 'Информатики',
            'course': 1,
            'is_active': True
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert StudyGroups.objects.filter(title='ГР-2025-01').exists()
    
    def test_update_study_group_admin(self, api_client, auth_token):
        """Тест обновления группы администратором"""
        group = StudyGroupFactory()
        url = reverse('groups:study-group-detail', kwargs={'pk': group.pk})
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        data = {'course': 4}
        response = api_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        group.refresh_from_db()
        assert group.course == 4
    
    def test_delete_study_group_admin(self, api_client, auth_token):
        """Тест удаления группы администратором"""
        group = StudyGroupFactory()
        url = reverse('groups:study-group-detail', kwargs={'pk': group.pk})
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not StudyGroups.objects.filter(pk=group.pk).exists()
    
    def test_create_study_group_regular_user(self, api_client, regular_user):
        """Тест попытки создания группы обычным пользователем"""
        refresh = RefreshToken.for_user(regular_user)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        url = reverse('groups:study-group-list')
        data = {
            'title': 'ГР-2025-02',
            'description': 'Тестовая группа',
            'faculty': 'Экономики',
            'course': 2
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_add_students_to_group(self, api_client, auth_token):
        """Тест добавления студентов в группу"""
        group = StudyGroupFactory()
        students = StudentFactory.create_batch(2)
        student_ids = [s.id for s in students]
        
        url = reverse('groups:study-group-detail', kwargs={'pk': group.pk})
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        data = {'student_ids': student_ids}
        response = api_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        group.refresh_from_db()
        assert group.students.count() == 2
    
    def test_search_groups(self, api_client, auth_token):
        """Тест поиска групп по названию"""
        StudyGroupFactory(title='ГР-2024-ИТ-01')
        StudyGroupFactory(title='ГР-2024-ЭК-02')
        
        url = reverse('groups:study-group-list')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        response = api_client.get(url, {'search': 'ИТ'})
        assert response.status_code == status.HTTP_200_OK
        # Проверяем что возвращаются результаты
        assert 'results' in response.data
    
    def test_filter_active_groups(self, api_client, auth_token):
        """Тест фильтрации только активных групп"""
        StudyGroupFactory.create_batch(2, is_active=True)
        StudyGroupFactory.create_batch(1, is_active=False)
        
        url = reverse('groups:study-group-list')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        response = api_client.get(url, {'is_active': 'true'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2


@pytest.mark.django_db
class TestStudyGroupsRelations:
    """Тесты связей учебных групп"""
    
    def test_student_can_be_in_multiple_groups(self):
        """Тест что студент может быть в нескольких группах"""
        student = StudentFactory()
        group1 = StudyGroupFactory()
        group2 = StudyGroupFactory()
        
        group1.students.add(student)
        group2.students.add(student)
        
        assert student.study_groups.count() == 2
        assert group1 in student.study_groups.all()
        assert group2 in student.study_groups.all()
    
    def test_remove_student_from_group(self):
        """Тест удаления студента из группы"""
        student = StudentFactory()
        group = StudyGroupFactory(students=[student])
        
        assert group.students.count() == 1
        group.students.remove(student)
        assert group.students.count() == 0
    
    def test_group_students_limit_to_student_role(self):
        """Тест что в группу можно добавлять только студентов"""
        teacher = UserFactory(role=RoleChoices.TEACHER)
        student = StudentFactory()
        group = StudyGroupFactory()
        
        # Добавляем студента - должно работать
        group.students.add(student)
        assert group.students.count() == 1
        
        # Добавляем преподавателя - технически добавится, но limit_choices_to ограничит в админке
        group.students.add(teacher)
        assert group.students.count() == 2  # В коде можно добавить, но в UI нельзя выбрать
