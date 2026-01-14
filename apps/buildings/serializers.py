from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from .models import Buildings, Audiences, AudiencesTypes


class AudiencesTypesSerializer(serializers.ModelSerializer):
    """Сериализатор для типов аудиторий"""
    
    class Meta:
        model = AudiencesTypes
        fields = ['id', 'title']
        read_only_fields = ['id']


class AudiencesListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка аудиторий (краткая информация)"""
    
    auditorium_type_name = serializers.CharField(
        source='auditorium_type.title',
        read_only=True
    )
    building_name = serializers.CharField(
        source='building.title',
        read_only=True
    )
    
    class Meta:
        model = Audiences
        fields = [
            'id',
            'title',
            'auditorium_number',
            'auditorium_type',
            'auditorium_type_name',
            'floor_number',
            'building',
            'building_name',
        ]
        read_only_fields = ['id', 'title']


class AudiencesDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детальной информации об аудитории"""
    
    auditorium_type_details = AudiencesTypesSerializer(
        source='auditorium_type',
        read_only=True
    )
    building_name = serializers.CharField(
        source='building.title',
        read_only=True
    )
    building_address = serializers.CharField(
        source='building.address',
        read_only=True
    )
    
    class Meta:
        model = Audiences
        fields = [
            'id',
            'title',
            'auditorium_number',
            'auditorium_type',
            'auditorium_type_details',
            'floor_number',
            'building',
            'building_name',
            'building_address',
        ]
        read_only_fields = ['id', 'title']


class AudiencesCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления аудитории"""
    
    class Meta:
        model = Audiences
        fields = [
            'auditorium_number',
            'auditorium_type',
            'floor_number',
            'building',
            'title',
        ]
        extra_kwargs = {
            'title': {'required': False, 'allow_blank': True}
        }

    def validate_auditorium_number(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                _("Номер аудитории должен быть положительным числом.")
            )
        return value

    def validate_floor_number(self, value):
        if value < 0:
            raise serializers.ValidationError(
                _("Номер этажа не может быть отрицательным.")
            )
        return value


class BuildingsListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка зданий (краткая информация)"""
    
    country_name = serializers.CharField(source='country.name', read_only=True)
    audiences_count = serializers.IntegerField(
        source='audiences.count',
        read_only=True
    )
    
    class Meta:
        model = Buildings
        fields = [
            'id',
            'title',
            'country',
            'country_name',
            'city',
            'address',
            'audiences_count',
        ]
        read_only_fields = ['id', 'address']


class BuildingsDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детальной информации о здании"""
    
    country_name = serializers.CharField(source='country.name', read_only=True)
    audiences = AudiencesListSerializer(many=True, read_only=True)
    audiences_count = serializers.IntegerField(
        source='audiences.count',
        read_only=True
    )
    
    class Meta:
        model = Buildings
        fields = [
            'id',
            'title',
            'country',
            'country_name',
            'region',
            'city',
            'street',
            'house_number',
            'address',
            'audiences',
            'audiences_count',
        ]
        read_only_fields = ['id', 'address']


class BuildingsCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления здания"""
    
    class Meta:
        model = Buildings
        fields = [
            'title',
            'country',
            'region',
            'city',
            'street',
            'house_number',
        ]

    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(
                _("Название строения не может быть пустым.")
            )
        return value.strip()

    def validate_city(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(
                _("Город не может быть пустым.")
            )
        return value.strip()

    def validate_street(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(
                _("Улица не может быть пустой.")
            )
        return value.strip()

    def validate_house_number(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(
                _("Номер дома не может быть пустым.")
            )
        return value.strip()
