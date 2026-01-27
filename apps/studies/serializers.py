from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .models import TimeSlot, Day, SubjectsTypes, SubjectSchedule, Subjects
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


class SubjectScheduleListSerializer(serializers.ModelSerializer):
    """Сериализатор для расписания предмета (краткая информация)"""
    
    week_day_name = serializers.CharField(source='week_day.title', read_only=True)
    time_slot_display = serializers.SerializerMethodField()
    subject_title = serializers.CharField(source='subject.title', read_only=True)
    subject_type = serializers.CharField(source='subject.subject_type.title', read_only=True)
    audience_details = serializers.SerializerMethodField()
    teachers_details = serializers.SerializerMethodField()
    groups_details = serializers.SerializerMethodField()
    
    class Meta:
        model = SubjectSchedule
        fields = [
            'id',
            'subject',
            'subject_title',
            'subject_type',
            'week_day',
            'week_day_name',
            'time_slot',
            'time_slot_display',
            'week_type',
            'audience_details',
            'teachers_details',
            'groups_details',
        ]
        read_only_fields = ['id']
    
    def get_time_slot_display(self, obj):
        return str(obj.time_slot)
    
    def get_audience_details(self, obj):
        """Получить информацию об аудитории"""
        audience = obj.subject.audience
        return {
            'id': audience.id,
            'title': audience.title,
            'number': audience.auditorium_number,
            'floor': audience.floor_number,
            'building': audience.building.title,
        }
    
    def get_teachers_details(self, obj):
        """Получить информацию о преподавателях"""
        teachers = obj.teachers.all()
        return [
            {
                'id': t.id,
                'username': t.username,
                'full_name': f"{t.last_name} {t.first_name}" if t.first_name and t.last_name else t.username,
            }
            for t in teachers
        ]
    
    def get_groups_details(self, obj):
        """Получить информацию о группах"""
        groups = obj.groups.all()
        return [
            {
                'id': g.id,
                'title': g.title,
            }
            for g in groups
        ]


class SubjectScheduleDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детальной информации о расписании предмета"""
    
    week_day_details = DaySerializer(source='week_day', read_only=True)
    time_slot_details = TimeSlotSerializer(source='time_slot', read_only=True)
    teachers_details = serializers.SerializerMethodField()
    groups_details = serializers.SerializerMethodField()
    
    class Meta:
        model = SubjectSchedule
        fields = [
            'id',
            'subject',
            'week_day',
            'week_day_details',
            'time_slot',
            'time_slot_details',
            'week_type',
            'teachers',
            'teachers_details',
            'groups',
            'groups_details',
        ]
        read_only_fields = ['id']
    
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


class SubjectScheduleCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления расписания предмета"""
    
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
        model = SubjectSchedule
        fields = ['subject', 'week_day', 'time_slot', 'week_type', 'teacher_ids', 'group_ids']
    
    def validate(self, data):
        # Проверяем уникальность комбинации
        instance = self.instance
        filters = {
            'subject': data.get('subject'),
            'week_day': data.get('week_day'),
            'time_slot': data.get('time_slot'),
            'week_type': data.get('week_type', 'BOTH')
        }
        
        # Исключаем текущий объект при обновлении
        qs = SubjectSchedule.objects.filter(**filters)
        if instance:
            qs = qs.exclude(pk=instance.pk)
        
        if qs.exists():
            raise serializers.ValidationError(
                _('Такое расписание уже существует для этого предмета.')
            )
        
        return data


class SubjectsListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка предметов (краткая информация)"""
    
    subject_type_name = serializers.CharField(source='subject_type.title', read_only=True)
    audience_name = serializers.CharField(source='audience.title', read_only=True)
    schedules_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Subjects
        fields = [
            'id',
            'title',
            'subject_type',
            'subject_type_name',
            'audience',
            'audience_name',
            'schedules_count',
        ]
        read_only_fields = ['id']
    
    def get_schedules_count(self, obj):
        """Получить количество расписаний для предмета"""
        return obj.schedules.count()


class SubjectsDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детальной информации о предмете"""
    
    subject_type_details = SubjectsTypesSerializer(source='subject_type', read_only=True)
    schedule_details = SubjectScheduleListSerializer(source='schedules', many=True, read_only=True)
    
    audience_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Subjects
        fields = [
            'id',
            'title',
            'subject_type',
            'subject_type_details',
            'schedule_details',
            'audience',
            'audience_details',
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


class SubjectsCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления предмета"""
    
    class Meta:
        model = Subjects
        fields = [
            'id',
            'title',
            'subject_type',
            'audience',
        ]
    
    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(
                _("Название предмета не может быть пустым.")
            )
        return value.strip()


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


class ScheduleGenerationRequestSerializer(serializers.Serializer):
    """Сериализатор запроса на генерацию расписания"""
    
    group_id = serializers.IntegerField(
        required=True,
        help_text=_('ID группы для генерации расписания')
    )
    subject_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        help_text=_('Список ID предметов для генерации расписания')
    )
    clear_existing = serializers.BooleanField(
        default=False,
        help_text=_('Очистить существующее расписание перед генерацией')
    )
    prefer_morning = serializers.BooleanField(
        default=True,
        help_text=_('Приоритет утренних пар')
    )
    time_range = serializers.ChoiceField(
        choices=['morning', 'mixed', 'afternoon', 'evening', 'full'],
        required=False,
        allow_null=True,
        help_text=_(
            'Предустановленный временной промежуток: '
            'morning (08:00-14:30), mixed (11:30-17:00), '
            'afternoon (13:00-18:20), evening (16:00-21:00), full (весь день)'
        )
    )
    custom_start_time = serializers.TimeField(
        required=False,
        allow_null=True,
        help_text=_('Кастомное время начала (HH:MM), имеет приоритет над time_range')
    )
    custom_end_time = serializers.TimeField(
        required=False,
        allow_null=True,
        help_text=_('Кастомное время окончания (HH:MM), требует custom_start_time')
    )
    start_day_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text=_('ID начального дня недели (например, понедельник). Если не указано, используются все дни')
    )
    end_day_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text=_('ID конечного дня недели (например, пятница). Если не указано, используются все дни')
    )
    
    def validate(self, attrs):
        # Если указано custom_end_time, должно быть и custom_start_time
        if attrs.get('custom_end_time') and not attrs.get('custom_start_time'):
            raise serializers.ValidationError({
                'custom_start_time': _('Необходимо указать время начала')
            })
        
        # Проверка, что время начала < времени окончания
        if attrs.get('custom_start_time') and attrs.get('custom_end_time'):
            if attrs['custom_start_time'] >= attrs['custom_end_time']:
                raise serializers.ValidationError({
                    'custom_end_time': _('Время окончания должно быть больше времени начала')
                })
        
        # Если указан end_day_id, должен быть и start_day_id
        if attrs.get('end_day_id') and not attrs.get('start_day_id'):
            raise serializers.ValidationError({
                'start_day_id': _('Необходимо указать начальный день недели')
            })
        
        # Проверка, что дни недели существуют
        from .models import Day
        if attrs.get('start_day_id'):
            if not Day.objects.filter(id=attrs['start_day_id']).exists():
                raise serializers.ValidationError({
                    'start_day_id': _('День недели с указанным ID не найден')
                })
        
        if attrs.get('end_day_id'):
            if not Day.objects.filter(id=attrs['end_day_id']).exists():
                raise serializers.ValidationError({
                    'end_day_id': _('День недели с указанным ID не найден')
                })
        
        return attrs
    
    def validate_group_id(self, value):
        # Проверяем существование группы
        from apps.groups.models import StudyGroups
        if not StudyGroups.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                _('Группа не найдена в системе')
            )
        
        return value
    
    def validate_subject_ids(self, value):
        if not value:
            raise serializers.ValidationError(
                _('Необходимо указать хотя бы один предмет')
            )
        
        # Проверяем существование предметов
        from .models import Subjects
        existing_subjects = Subjects.objects.filter(id__in=value)
        if existing_subjects.count() != len(value):
            raise serializers.ValidationError(
                _('Некоторые предметы не найдены в системе')
            )
        
        return value


class ScheduleGenerationResponseSerializer(serializers.Serializer):
    """Сериализатор ответа на генерацию расписания"""
    
    success = serializers.BooleanField()
    messages = serializers.ListField(child=serializers.CharField())
    statistics = serializers.DictField()


class ScheduleValidationResponseSerializer(serializers.Serializer):
    """Сериализатор ответа на валидацию расписания"""
    
    is_valid = serializers.BooleanField()
    conflicts = serializers.ListField(child=serializers.CharField())


class ScheduleStatisticsSerializer(serializers.Serializer):
    """Сериализатор статистики расписания"""
    
    total_groups = serializers.IntegerField()
    total_subjects = serializers.IntegerField()
    subjects_with_schedule = serializers.IntegerField()
    subjects_without_schedule = serializers.IntegerField()
    total_schedule_slots = serializers.IntegerField()
    average_slots_per_subject = serializers.FloatField()


class TimeRangeSerializer(serializers.Serializer):
    """Сериализатор для временного промежутка"""
    
    name = serializers.CharField()
    start_time = serializers.CharField()
    end_time = serializers.CharField()
    description = serializers.CharField()


class AvailableTimeRangesSerializer(serializers.Serializer):
    """Сериализатор для списка доступных временных промежутков"""
    
    morning = TimeRangeSerializer()
    mixed = TimeRangeSerializer()
    afternoon = TimeRangeSerializer()
    evening = TimeRangeSerializer()
    full = TimeRangeSerializer()

