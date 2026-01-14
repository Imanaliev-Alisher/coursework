from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .models import StudyGroups

User = get_user_model()


class StudentBriefSerializer(serializers.ModelSerializer):
    """Краткая информация о студенте для отображения в группе"""
    
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name']
        read_only_fields = ['id', 'username', 'email', 'first_name', 'last_name']
    
    def get_full_name(self, obj):
        if obj.first_name and obj.last_name:
            return f"{obj.last_name} {obj.first_name}"
        return obj.username


class StudyGroupsListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка учебных групп (краткая информация)"""
    
    students_count = serializers.IntegerField(
        source='students.count',
        read_only=True
    )
    
    class Meta:
        model = StudyGroups
        fields = [
            'id',
            'title',
            'description',
            'faculty',
            'course',
            'is_active',
            'students_count',
        ]
        read_only_fields = ['id']


class StudyGroupsDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детальной информации об учебной группе"""
    
    students = StudentBriefSerializer(many=True, read_only=True)
    students_count = serializers.IntegerField(
        source='students.count',
        read_only=True
    )
    
    class Meta:
        model = StudyGroups
        fields = [
            'id',
            'title',
            'description',
            'faculty',
            'course',
            'is_active',
            'students',
            'students_count',
        ]
        read_only_fields = ['id']


class StudyGroupsCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления учебной группы"""
    
    student_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='STUDENT'),
        many=True,
        write_only=True,
        required=False,
        source='students'
    )
    
    class Meta:
        model = StudyGroups
        fields = [
            'title',
            'description',
            'faculty',
            'course',
            'is_active',
            'student_ids',
        ]
    
    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(
                _("Наименование учебной группы не может быть пустым.")
            )
        return value.strip()
    
    def validate_description(self, value):
        if value and len(value) > 1000:
            raise serializers.ValidationError(
                _("Описание не должно превышать 1000 символов.")
            )
        return value
    
    def create(self, validated_data):
        students_data = validated_data.pop('students', [])
        study_group = StudyGroups.objects.create(**validated_data)
        if students_data:
            study_group.students.set(students_data)
        return study_group
    
    def update(self, instance, validated_data):
        students_data = validated_data.pop('students', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if students_data is not None:
            instance.students.set(students_data)
        
        return instance


class AddStudentsSerializer(serializers.Serializer):
    """Сериализатор для добавления студентов в группу"""
    
    student_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='STUDENT'),
        many=True,
        required=True
    )
    
    def validate_student_ids(self, value):
        if not value:
            raise serializers.ValidationError(
                _("Необходимо указать хотя бы одного студента.")
            )
        return value


class RemoveStudentsSerializer(serializers.Serializer):
    """Сериализатор для удаления студентов из группы"""
    
    student_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='STUDENT'),
        many=True,
        required=True
    )
    
    def validate_student_ids(self, value):
        if not value:
            raise serializers.ValidationError(
                _("Необходимо указать хотя бы одного студента.")
            )
        return value
