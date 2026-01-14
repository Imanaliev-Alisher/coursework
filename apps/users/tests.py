"""
Тесты для приложения users
Покрытие: модели, сериализаторы, представления, permissions
"""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .factories import UserFactory, StudentFactory, TeacherFactory, AdminFactory
from .models import User
from .choices import RoleChoices
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    ChangePasswordSerializer, StudentSerializer, TeacherSerializer
)

pytestmark = pytest.mark.django_db

User = get_user_model()


# ==================== Тесты моделей ====================

class TestUserModel:
    """Тесты модели User"""
    
    def test_create_user(self):
        """Тест создания обычного пользователя"""
        user = UserFactory(username='testuser', email='test@example.com')
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.is_active
        assert not user.is_staff
        assert not user.is_superuser
    
    def test_create_student(self):
        """Тест создания студента"""
        student = StudentFactory()
        assert student.role == 'STUDENT'
        assert not student.is_staff
    
    def test_create_teacher(self):
        """Тест создания преподавателя"""
        teacher = TeacherFactory()
        assert teacher.role == 'TEACHER'
        assert teacher.department
        assert teacher.phone
        assert teacher.office
    
    def test_create_superuser(self):
        """Тест создания суперпользователя"""
        admin = AdminFactory()
        assert admin.is_staff
        assert admin.is_superuser
    
    def test_user_str_representation(self):
        """Тест строкового представления пользователя"""
        user = UserFactory(username='testuser')
        assert str(user) == 'testuser'
    
    def test_user_email_required(self):
        """Тест обязательности email"""
        user = UserFactory()
        assert user.email


# ==================== Тесты сериализаторов ====================

class TestUserSerializers:
    """Тесты сериализаторов пользователей"""
    
    def test_user_serializer(self):
        """Тест UserSerializer"""
        user = UserFactory()
        serializer = UserSerializer(user)
        data = serializer.data
        
        assert 'id' in data
        assert 'username' in data
        assert 'email' in data
        assert 'role' in data
        assert 'password' not in data
    
    def test_user_create_serializer_valid(self):
        """Тест создания пользователя с валидными данными"""
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'TestPass123!',
            'password_confirm': 'TestPass123!',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'STUDENT'
        }
        serializer = UserCreateSerializer(data=data)
        assert serializer.is_valid()
        user = serializer.save()
        assert user.username == 'newuser'
        assert user.check_password('TestPass123!')
    
    def test_user_create_serializer_password_mismatch(self):
        """Тест создания пользователя с несовпадающими паролями"""
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'TestPass123!',
            'password_confirm': 'DifferentPass123!',
            'role': 'STUDENT'
        }
        serializer = UserCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors
    
    def test_user_update_serializer(self):
        """Тест обновления пользователя"""
        user = UserFactory()
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@test.com'
        }
        serializer = UserUpdateSerializer(user, data=data, partial=True)
        assert serializer.is_valid()
        updated_user = serializer.save()
        assert updated_user.first_name == 'Updated'
    
    def test_student_serializer(self):
        """Тест StudentSerializer"""
        student = StudentFactory()
        serializer = StudentSerializer(student)
        data = serializer.data
        
        assert data['id'] == student.id
        assert 'study_groups' in data
    
    def test_teacher_serializer(self):
        """Тест TeacherSerializer"""
        teacher = TeacherFactory()
        serializer = TeacherSerializer(teacher)
        data = serializer.data
        
        assert data['id'] == teacher.id
        assert 'department' in data
        assert 'phone' in data
        assert 'office' in data


# ==================== Тесты API ====================

class TestUserAPI:
    """Тесты API пользователей"""
    
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    @pytest.fixture
    def admin_user(self):
        return AdminFactory()
    
    @pytest.fixture
    def regular_user(self):
        return UserFactory()
    
    @pytest.fixture
    def admin_token(self, admin_user):
        refresh = RefreshToken.for_user(admin_user)
        return str(refresh.access_token)
    
    @pytest.fixture
    def user_token(self, regular_user):
        refresh = RefreshToken.for_user(regular_user)
        return str(refresh.access_token)
    
    def test_create_user_unauthenticated(self, api_client):
        """Тест создания пользователя без аутентификации"""
        url = reverse('users:user-list')
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'TestPass123!',
            'password_confirm': 'TestPass123!',
            'role': 'STUDENT'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(username='newuser').exists()
    
    def test_list_users_admin(self, api_client, admin_token):
        """Тест получения списка пользователей администратором"""
        UserFactory.create_batch(5)
        url = reverse('users:user-list')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0
    
    def test_list_users_regular_user(self, api_client, user_token):
        """Тест получения списка пользователей обычным пользователем"""
        url = reverse('users:user-list')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {user_token}')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_current_user(self, api_client, user_token, regular_user):
        """Тест получения информации о текущем пользователе"""
        url = reverse('users:user-me')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {user_token}')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == regular_user.id
    
    def test_change_password(self, api_client, user_token, regular_user):
        """Тест смены пароля"""
        url = reverse('users:user-change-password')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {user_token}')
        data = {
            'old_password': 'testpass123',
            'new_password': 'NewPass123!',
            'new_password_confirm': 'NewPass123!'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        
        # Проверяем, что пароль изменился
        regular_user.refresh_from_db()
        assert regular_user.check_password('NewPass123!')
    
    def test_change_password_wrong_old_password(self, api_client, user_token):
        """Тест смены пароля с неверным старым паролем"""
        url = reverse('users:user-change-password')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {user_token}')
        data = {
            'old_password': 'wrongpassword',
            'new_password': 'NewPass123!',
            'new_password_confirm': 'NewPass123!'
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_update_user_owner(self, api_client, user_token, regular_user):
        """Тест обновления пользователя владельцем"""
        url = reverse('users:user-detail', kwargs={'pk': regular_user.pk})
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {user_token}')
        data = {'first_name': 'Updated'}
        response = api_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        regular_user.refresh_from_db()
        assert regular_user.first_name == 'Updated'
    
    def test_update_user_not_owner(self, api_client, user_token):
        """Тест обновления чужого пользователя"""
        other_user = UserFactory()
        url = reverse('users:user-detail', kwargs={'pk': other_user.pk})
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {user_token}')
        data = {'first_name': 'Hacked'}
        response = api_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_delete_user_admin(self, api_client):
        """Тест удаления пользователя администратором"""
        admin = AdminFactory()
        user = UserFactory()
        refresh = RefreshToken.for_user(admin)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        url = reverse('users:user-detail', kwargs={'pk': user.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not User.objects.filter(pk=user.pk).exists()


class TestStudentAPI:
    """Тесты API студентов"""
    
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    @pytest.fixture
    def auth_user(self):
        return UserFactory()
    
    @pytest.fixture
    def auth_token(self, auth_user):
        refresh = RefreshToken.for_user(auth_user)
        return str(refresh.access_token)
    
    def test_list_students(self, api_client):
        """Тест получения списка студентов"""
        # Создаем администратора для доступа
        admin = AdminFactory()
        refresh = RefreshToken.for_user(admin)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        # Очищаем существующих студентов кроме админа
        User.objects.filter(role=RoleChoices.STUDENT).delete()
        StudentFactory.create_batch(5)
        
        url = reverse('users:student-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 5
    
    def test_get_student_detail(self, api_client, auth_token):
        """Тест получения детальной информации о студенте"""
        student = StudentFactory()
        url = reverse('users:student-detail', kwargs={'pk': student.pk})
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == student.id


class TestTeacherAPI:
    """Тесты API преподавателей"""
    
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    @pytest.fixture
    def auth_user(self):
        return UserFactory()
    
    @pytest.fixture
    def auth_token(self, auth_user):
        refresh = RefreshToken.for_user(auth_user)
        return str(refresh.access_token)
    
    def test_list_teachers(self, api_client, auth_token):
        """Тест получения списка преподавателей"""
        TeacherFactory.create_batch(5)
        url = reverse('users:teacher-list')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 5
    
    def test_get_teacher_detail(self, api_client, auth_token):
        """Тест получения детальной информации о преподавателе"""
        teacher = TeacherFactory()
        url = reverse('users:teacher-detail', kwargs={'pk': teacher.pk})
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == teacher.id
        assert 'department' in response.data


# ==================== Тесты Permissions ====================

class TestUserPermissions:
    """Тесты прав доступа"""
    
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    def test_unauthenticated_access(self, api_client):
        """Тест доступа без аутентификации"""
        url = reverse('users:user-list')
        response = api_client.get(url)
        # JWT возвращает 401 для неаутентифицированных пользователей
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_admin_can_access_all(self, api_client):
        """Тест полного доступа администратора"""
        admin = AdminFactory()
        refresh = RefreshToken.for_user(admin)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('users:user-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
    
    def test_regular_user_limited_access(self, api_client):
        """Тест ограниченного доступа обычного пользователя"""
        user = UserFactory()
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Не может получить список всех пользователей
        url = reverse('users:user-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Но может получить свою информацию
        url = reverse('users:user-me')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK


# ==================== Тесты UserManager ====================

class TestUserManager:
    """Тесты менеджера пользователей"""
    
    def test_create_user_with_email(self):
        """Тест создания пользователя через менеджер"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.check_password('testpass123')
        assert not user.is_staff
        assert not user.is_superuser
    
    def test_create_superuser(self):
        """Тест создания суперпользователя через менеджер"""
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        assert admin.is_staff
        assert admin.is_superuser
    
    def test_create_user_without_email(self):
        """Тест создания пользователя без email"""
        with pytest.raises(ValueError):
            User.objects.create_user(
                username='testuser',
                email='',
                password='testpass123'
            )
    
    def test_create_superuser_not_staff(self):
        """Тест создания суперпользователя без is_staff"""
        with pytest.raises(ValueError):
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='adminpass123',
                is_staff=False
            )
    
    def test_create_superuser_not_superuser(self):
        """Тест создания суперпользователя без is_superuser"""
        with pytest.raises(ValueError):
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='adminpass123',
                is_superuser=False
            )


@pytest.mark.django_db
class TestUserPermissions2:
    """Дополнительные тесты прав доступа"""
    
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    def test_is_owner_or_admin_permission(self, api_client):
        """Тест разрешения IsOwnerOrAdmin"""
        user1 = UserFactory()
        user2 = UserFactory()
        
        # user1 пытается изменить user2
        refresh = RefreshToken.for_user(user1)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        url = reverse('users:user-detail', kwargs={'pk': user2.pk})
        data = {'first_name': 'Changed'}
        response = api_client.patch(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_admin_can_modify_any_user(self, api_client):
        """Тест изменения любого пользователя администратором"""
        admin = AdminFactory()
        user = UserFactory()
        
        refresh = RefreshToken.for_user(admin)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        url = reverse('users:user-detail', kwargs={'pk': user.pk})
        data = {'first_name': 'AdminChanged'}
        response = api_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        
        user.refresh_from_db()
        assert user.first_name == 'AdminChanged'
    
    def test_owner_can_modify_own_data(self, api_client):
        """Тест изменения собственных данных пользователем"""
        user = UserFactory()
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        url = reverse('users:user-detail', kwargs={'pk': user.pk})
        data = {'first_name': 'SelfChanged'}
        response = api_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        
        user.refresh_from_db()
        assert user.first_name == 'SelfChanged'


@pytest.mark.django_db
class TestPermissionClasses:
    """Тесты классов разрешений"""
    
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    def test_is_admin_or_read_only_read(self, api_client):
        """Тест IsAdminOrReadOnly для GET запроса"""
        user = UserFactory()
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        # Обычный пользователь может читать
        url = reverse('users:user-detail', kwargs={'pk': user.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
    
    def test_is_admin_permission(self, api_client):
        """Тест разрешения IsAdmin"""
        # Обычный пользователь не может получить список всех пользователей
        user = UserFactory()
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        url = reverse('users:user-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Админ может
        admin = AdminFactory()
        refresh = RefreshToken.for_user(admin)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

