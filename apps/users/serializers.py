from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения информации о пользователе"""
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'gender',
            'role',
            'department',
            'phone',
            'office',
            'is_active',
            'date_joined',
        ]
        read_only_fields = ['id', 'date_joined']


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания нового пользователя"""
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'password_confirm',
            'first_name',
            'last_name',
            'gender',
            'role',
            'department',
            'phone',
            'office',
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password": _("Пароли не совпадают.")
            })
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления информации о пользователе"""
    
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'gender',
            'email',
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """Сериализатор для смены пароля"""
    
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Неверный старый пароль."))
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password": _("Новые пароли не совпадают.")
            })
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class StudentSerializer(serializers.ModelSerializer):
    """Сериализатор для студентов"""
    
    study_groups = serializers.StringRelatedField(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'gender',
            'is_active',
            'study_groups',
        ]
        read_only_fields = ['id', 'study_groups']


class TeacherSerializer(serializers.ModelSerializer):
    """Сериализатор для преподавателей"""
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'department',
            'phone',
            'office',
            'first_name',
            'last_name',
            'gender',
            'is_active',
        ]
        read_only_fields = ['id']
