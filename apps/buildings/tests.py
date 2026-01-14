import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.factories import UserFactory, AdminFactory
from apps.users.models import User
from apps.users.choices import RoleChoices
from .factories import BuildingsFactory, AudiencesTypesFactory, AudiencesFactory
from .models import Buildings, AudiencesTypes, Audiences


@pytest.mark.django_db
class TestBuildingsModel:
    """Тесты модели Buildings"""
    
    def test_create_building(self):
        """Тест создания здания"""
        building = BuildingsFactory()
        assert building.id is not None
        assert building.title is not None
        assert building.country is not None
    
    def test_building_str_representation(self):
        """Тест строкового представления здания"""
        building = BuildingsFactory(title='Главный корпус')
        assert str(building) == 'Главный корпус'
    
    def test_building_address_auto_generation(self):
        """Тест автоматической генерации адреса"""
        building = BuildingsFactory(
            country='KG',
            region='Чуйская область',
            city='Бишкек',
            street='проспект Манаса',
            house_number='123',
            address=''
        )
        building.save()
        assert 'KG' in building.address
        assert 'Бишкек' in building.address
        assert 'проспект Манаса' in building.address
        assert '123' in building.address
    
    def test_building_address_without_region(self):
        """Тест генерации адреса без региона"""
        building = BuildingsFactory(
            country='KG',
            region='',
            city='Бишкек',
            street='улица Льва Толстого',
            house_number='45',
            address=''
        )
        building.save()
        assert 'KG' in building.address
        assert 'Бишкек' in building.address


@pytest.mark.django_db
class TestAudiencesTypesModel:
    """Тесты модели AudiencesTypes"""
    
    def test_create_audience_type(self):
        """Тест создания типа аудитории"""
        audience_type = AudiencesTypesFactory(title='Лекционная')
        assert audience_type.id is not None
        assert audience_type.title == 'Лекционная'
    
    def test_audience_type_str_representation(self):
        """Тест строкового представления типа аудитории"""
        audience_type = AudiencesTypesFactory(title='Компьютерный класс')
        assert str(audience_type) == 'Компьютерный класс'


@pytest.mark.django_db
class TestAudiencesModel:
    """Тесты модели Audiences"""
    
    def test_create_audience(self):
        """Тест создания аудитории"""
        audience = AudiencesFactory()
        assert audience.id is not None
        assert audience.auditorium_number is not None
        assert audience.building is not None
    
    def test_audience_title_auto_generation(self):
        """Тест автоматической генерации названия аудитории"""
        audience_type = AudiencesTypesFactory(title='Лекционная')
        audience = AudiencesFactory(
            auditorium_type=audience_type,
            auditorium_number=101,
            title=''
        )
        audience.save()
        assert audience.title == 'Лекционная 101'
    
    def test_audience_custom_title(self):
        """Тест пользовательского названия аудитории"""
        audience = AudiencesFactory(title='Актовый зал')
        assert audience.title == 'Актовый зал'
    
    def test_audience_str_representation(self):
        """Тест строкового представления аудитории"""
        audience = AudiencesFactory(title='Зал 305')
        assert str(audience) == 'Зал 305'


@pytest.mark.django_db
class TestBuildingsAPI:
    """Тесты API для зданий"""
    
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
    
    def test_list_buildings(self, api_client, auth_token):
        """Тест получения списка зданий"""
        BuildingsFactory.create_batch(3)
        url = reverse('buildings:building-list')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3
    
    def test_get_building_detail(self, api_client, auth_token):
        """Тест получения детальной информации о здании"""
        building = BuildingsFactory()
        url = reverse('buildings:building-detail', kwargs={'pk': building.pk})
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == building.title
    
    def test_create_building_admin(self, api_client, auth_token):
        """Тест создания здания администратором"""
        url = reverse('buildings:building-list')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        data = {
            'title': 'Новый корпус',
            'country': 'KG',
            'city': 'Бишкек',
            'street': 'улица Тестовая',
            'house_number': '999'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Buildings.objects.filter(title='Новый корпус').exists()
    
    def test_update_building_admin(self, api_client, auth_token):
        """Тест обновления здания администратором"""
        building = BuildingsFactory()
        url = reverse('buildings:building-detail', kwargs={'pk': building.pk})
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        data = {'title': 'Обновленное название'}
        response = api_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        building.refresh_from_db()
        assert building.title == 'Обновленное название'
    
    def test_delete_building_admin(self, api_client, auth_token):
        """Тест удаления здания администратором"""
        building = BuildingsFactory()
        url = reverse('buildings:building-detail', kwargs={'pk': building.pk})
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Buildings.objects.filter(pk=building.pk).exists()
    
    def test_create_building_regular_user(self, api_client, regular_user):
        """Тест попытки создания здания обычным пользователем"""
        refresh = RefreshToken.for_user(regular_user)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        url = reverse('buildings:building-list')
        data = {
            'title': 'Новый корпус',
            'country': 'KG',
            'city': 'Бишкек',
            'street': 'улица Тестовая',
            'house_number': '999'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestAudiencesTypesAPI:
    """Тесты API для типов аудиторий"""
    
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
    
    def test_list_audience_types(self, api_client, auth_token):
        """Тест получения списка типов аудиторий"""
        AudiencesTypesFactory.create_batch(4)
        url = reverse('buildings:audience-type-list')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 4
    
    def test_create_audience_type_admin(self, api_client, auth_token):
        """Тест создания типа аудитории администратором"""
        url = reverse('buildings:audience-type-list')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        data = {'title': 'Спортивный зал'}
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert AudiencesTypes.objects.filter(title='Спортивный зал').exists()


@pytest.mark.django_db
class TestAudiencesAPI:
    """Тесты API для аудиторий"""
    
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
    
    def test_list_audiences(self, api_client, auth_token):
        """Тест получения списка аудиторий"""
        AudiencesFactory.create_batch(5)
        url = reverse('buildings:audience-list')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 5
    
    def test_get_audience_detail(self, api_client, auth_token):
        """Тест получения детальной информации об аудитории"""
        audience = AudiencesFactory()
        url = reverse('buildings:audience-detail', kwargs={'pk': audience.pk})
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['auditorium_number'] == audience.auditorium_number
    
    def test_create_audience_admin(self, api_client, auth_token):
        """Тест создания аудитории администратором"""
        building = BuildingsFactory()
        audience_type = AudiencesTypesFactory()
        url = reverse('buildings:audience-list')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        data = {
            'auditorium_number': 202,
            'auditorium_type': audience_type.id,
            'floor_number': 2,
            'building': building.id
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Audiences.objects.filter(auditorium_number=202).exists()
    
    def test_filter_audiences_by_building(self, api_client, auth_token):
        """Тест фильтрации аудиторий по зданию"""
        building1 = BuildingsFactory()
        building2 = BuildingsFactory()
        AudiencesFactory.create_batch(3, building=building1)
        AudiencesFactory.create_batch(2, building=building2)
        
        url = reverse('buildings:audience-list')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        response = api_client.get(url, {'building': building1.id})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3
    
    def test_create_audience_regular_user(self, api_client, regular_user):
        """Тест попытки создания аудитории обычным пользователем"""
        refresh = RefreshToken.for_user(regular_user)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        
        building = BuildingsFactory()
        audience_type = AudiencesTypesFactory()
        url = reverse('buildings:audience-list')
        data = {
            'auditorium_number': 303,
            'auditorium_type': audience_type.id,
            'floor_number': 3,
            'building': building.id
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_update_audience_admin(self, api_client, auth_token):
        """Тест обновления аудитории администратором"""
        audience = AudiencesFactory()
        url = reverse('buildings:audience-detail', kwargs={'pk': audience.pk})
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        data = {'floor_number': 5}
        response = api_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        audience.refresh_from_db()
        assert audience.floor_number == 5


@pytest.mark.django_db
class TestBuildingsSerializers:
    """Тесты сериализаторов зданий"""
    
    def test_audience_title_auto_generated_on_create(self):
        """Тест автоматической генерации названия аудитории при создании"""
        audience_type = AudiencesTypesFactory(title='Лабораторная')
        building = BuildingsFactory()
        audience = AudiencesFactory(
            auditorium_type=audience_type,
            auditorium_number=404,
            building=building,
            title=''
        )
        assert 'Лабораторная' in audience.title
        assert '404' in audience.title
