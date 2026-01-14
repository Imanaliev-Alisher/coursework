from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .models import TimeSlot, Day, SubjectsTypes, Schedule, Subjects, ScheduleOverride
from apps.buildings.models import Audiences
from apps.groups.models import StudyGroups

User = get_user_model()


class TimeSlotSerializer(serializers.ModelSerializer):
    """Сериализатор для временных слотов (пар)"""
    
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = TimeSlot
        fields = ['id', 'number', 'start_time', 'end_time', 'display_name']
        read_only_fields = ['id']
    
    def get_display_name(self, obj):
        return str(obj)
    
    def validate(self, data):
        if data.get('start_time') and data.get('end_time'):
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError(
                    _('Время начала должно быть меньше времени окончания.')
                )
        return data


class DaySerializer(serializers.ModelSerializer):
    """Сериализатор для дней недели"""
    
    class Meta:
        model = Day
        fields = ['id', 'title']
        read_only_fields = ['id']


class SubjectsTypesSerializer(serializers.ModelSerializer):
    """Сериализатор для типов предметов"""
    
    class Meta:
        model = SubjectsTypes
        fields = ['id', 'title']
        read_only_fields = ['id']


class ScheduleListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка расписаний (краткая информация)"""
    
    week_day_name = serializers.CharField(source='week_day.title', read_only=True)
    time_slot_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Schedule
        fields = [
            'id',
            'week_day',
            'week_day_name',
            'time_slot',
            'time_slot_display',
            'week_type',
        ]
        read_only_fields = ['id']
    
    def get_time_slot_display(self, obj):
        return str(obj.time_slot)


class ScheduleDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детальной информации о расписании"""
    
    week_day_details = DaySerializer(source='week_day', read_only=True)
    time_slot_details = TimeSlotSerializer(source='time_slot', read_only=True)
    
    class Meta:
        model = Schedule
        fields = [
            'id',
            'week_day',
            'week_day_details',
            'time_slot',
            'time_slot_details',
            'week_type',
        ]
        read_only_fields = ['id']


class ScheduleCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления расписания"""
    
    class Meta:
        model = Schedule
        fields = ['week_day', 'time_slot', 'week_type']
    
    def validate(self, data):
        # Проверка уникальности комбинации
        instance = self.instance
        queryset = Schedule.objects.filter(
            week_day=data.get('week_day'),
            time_slot=data.get('time_slot'),
            week_type=data.get('week_type')
        )
        
        if instance:
            queryset = queryset.exclude(pk=instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError(
                _('Расписание с такой комбинацией дня, времени и типа недели уже существует.')
            )
        
        return data


class SubjectsListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка предметов (краткая информация)"""
    
    subject_type_name = serializers.CharField(source='subject_type.title', read_only=True)
    audience_name = serializers.CharField(source='audience.title', read_only=True)
    teachers_count = serializers.IntegerField(source='teachers.count', read_only=True)
    groups_count = serializers.IntegerField(source='groups.count', read_only=True)
    
    class Meta:
        model = Subjects
        fields = [
            'id',
            'title',
            'subject_type',
            'subject_type_name',
            'audience',
            'audience_name',
            'teachers_count',
            'groups_count',
        ]
        read_only_fields = ['id']


class SubjectsDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детальной информации о предмете"""
    
    subject_type_details = SubjectsTypesSerializer(source='subject_type', read_only=True)
    schedule_details = ScheduleListSerializer(source='schedule', many=True, read_only=True)
    
    audience_details = serializers.SerializerMethodField()
    teachers_details = serializers.SerializerMethodField()
    groups_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Subjects
        fields = [
            'id',
            'title',
            'subject_type',
            'subject_type_details',
            'schedule',
            'schedule_details',
            'audience',
            'audience_details',
            'teachers',
            'teachers_details',
            'groups',
            'groups_details',
        ]
        read_only_fields = ['id']
    
    def get_audience_details(self, obj):
        return {
            'id': obj.audience.id,
            'title': obj.audience.title,
            'number': obj.audience.auditorium_number,
            'floor': obj.audience.floor_number,
            'building': obj.audience.building.title,
        }
    
    def get_teachers_details(self, obj):
        teachers = obj.teachers.all()
        return [
            {
                'id': t.id,
                'username': t.username,
                'full_name': f"{t.last_name} {t.first_name}" if t.first_name and t.last_name else t.username,
                'email': t.email,
            }
            for t in teachers
        ]
    
    def get_groups_details(self, obj):
        groups = obj.groups.all()
        return [
            {
                'id': g.id,
                'title': g.title,
                'is_active': g.is_active,
                'students_count': g.students.count(),
            }
            for g in groups
        ]


class SubjectsCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления предмета"""
    
    schedule_ids = serializers.PrimaryKeyRelatedField(
        queryset=Schedule.objects.all(),
        many=True,
        write_only=True,
        source='schedule',
        required=False
    )
    teacher_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='TEACHER'),
        many=True,
        write_only=True,
        source='teachers',
        required=False
    )
    group_ids = serializers.PrimaryKeyRelatedField(
        queryset=StudyGroups.objects.filter(is_active=True),
        many=True,
        write_only=True,
        source='groups',
        required=False
    )
    
    class Meta:
        model = Subjects
        fields = [
            'title',
            'subject_type',
            'audience',
            'schedule_ids',
            'teacher_ids',
            'group_ids',
        ]
    
    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(
                _("Название предмета не может быть пустым.")
            )
        return value.strip()
    
    def create(self, validated_data):
        schedule_data = validated_data.pop('schedule', [])
        teachers_data = validated_data.pop('teachers', [])
        groups_data = validated_data.pop('groups', [])
        
        subject = Subjects.objects.create(**validated_data)
        
        if schedule_data:
            subject.schedule.set(schedule_data)
        if teachers_data:
            subject.teachers.set(teachers_data)
        if groups_data:
            subject.groups.set(groups_data)
        
        return subject
    
    def update(self, instance, validated_data):
        schedule_data = validated_data.pop('schedule', None)
        teachers_data = validated_data.pop('teachers', None)
        groups_data = validated_data.pop('groups', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if schedule_data is not None:
            instance.schedule.set(schedule_data)
        if teachers_data is not None:
            instance.teachers.set(teachers_data)
        if groups_data is not None:
            instance.groups.set(groups_data)
        
        return instance


class TimetableSerializer(serializers.Serializer):
    """Сериализатор для расписания (представление в виде таблицы)"""
    
    day = serializers.CharField()
    time_slot = serializers.CharField()
    subject = serializers.CharField()
    subject_type = serializers.CharField()
    audience = serializers.CharField()
    teachers = serializers.ListField(child=serializers.CharField())
    groups = serializers.ListField(child=serializers.CharField())
    week_type = serializers.CharField()


class ScheduleOverrideSerializer(serializers.ModelSerializer):
    """Сериализатор для переопределений расписания"""
    
    subject_title = serializers.CharField(source='subject.title', read_only=True)
    time_slot_display = serializers.CharField(source='time_slot.__str__', read_only=True)
    audience_display = serializers.CharField(source='audience.__str__', read_only=True, allow_null=True)
    
    class Meta:
        model = ScheduleOverride
        fields = [
            'id',
            'subject',
            'subject_title',
            'date',
            'time_slot',
            'time_slot_display',
            'audience',
            'audience_display',
            'is_cancelled',
            'notes',
        ]
        read_only_fields = ['id']
    
    def validate_date(self, value):
        """Проверка, что дата не в прошлом"""
        from django.utils import timezone
        if value < timezone.now().date():
            raise serializers.ValidationError(
                _('Нельзя создавать переопределения для прошедших дат.')
            )
        return value


class ScheduleOverrideCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления переопределений расписания"""
    
    class Meta:
        model = ScheduleOverride
        fields = [
            'subject',
            'date',
            'time_slot',
            'audience',
            'is_cancelled',
            'notes',
        ]

