from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.utils.translation import gettext_lazy as _
from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from apps.users.permissions import IsAdminOrReadOnly

from .models import TimeSlot, Day, SubjectsTypes, SubjectSchedule, Subjects
from .serializers import (
    TimeSlotSerializer,
    DaySerializer,
    SubjectsTypesSerializer,
    SubjectScheduleListSerializer,
    SubjectScheduleDetailSerializer,
    SubjectScheduleCreateUpdateSerializer,
    SubjectsListSerializer,
    SubjectsDetailSerializer,
    SubjectsCreateUpdateSerializer,
    TimetableSerializer,
    ScheduleGenerationRequestSerializer,
    ScheduleGenerationResponseSerializer,
    ScheduleValidationResponseSerializer,
    ScheduleStatisticsSerializer,
    AvailableTimeRangesSerializer,
)
from .export_utils import generate_pdf_timetable, generate_excel_timetable
from .schedule_generator import (
    generate_schedule_for_group,
    validate_generated_schedule,
    get_schedule_statistics,
    get_available_time_ranges
)
from .validators import check_schedule_conflicts


@extend_schema_view(
    list=extend_schema(
        summary="Получить список временных слотов",
        description="Возвращает список всех временных слотов (пар)",
        tags=["Временные слоты"]
    ),
    retrieve=extend_schema(
        summary="Получить временной слот",
        description="Возвращает информацию о временном слоте",
        tags=["Временные слоты"]
    ),
    create=extend_schema(
        summary="Создать временной слот",
        description="Создает новый временной слот (пару)",
        tags=["Временные слоты"]
    ),
    update=extend_schema(
        summary="Обновить временной слот",
        description="Обновляет временной слот",
        tags=["Временные слоты"]
    ),
    partial_update=extend_schema(
        summary="Частично обновить временной слот",
        description="Частично обновляет временной слот",
        tags=["Временные слоты"]
    ),
    destroy=extend_schema(
        summary="Удалить временной слот",
        description="Удаляет временной слот",
        tags=["Временные слоты"]
    ),
)
class TimeSlotViewSet(viewsets.ModelViewSet):
    """ViewSet для управления временными слотами (парами)"""
    
    queryset = TimeSlot.objects.all()
    serializer_class = TimeSlotSerializer
    permission_classes = [IsAdminOrReadOnly]
    ordering = ['number']


@extend_schema_view(
    list=extend_schema(
        summary="Получить список дней недели",
        description="Возвращает список всех дней недели",
        tags=["Дни недели"]
    ),
    retrieve=extend_schema(
        summary="Получить день недели",
        description="Возвращает информацию о дне недели",
        tags=["Дни недели"]
    ),
    create=extend_schema(
        summary="Создать день недели",
        description="Создает новый день недели",
        tags=["Дни недели"]
    ),
    update=extend_schema(
        summary="Обновить день недели",
        description="Обновляет день недели",
        tags=["Дни недели"]
    ),
    partial_update=extend_schema(
        summary="Частично обновить день недели",
        description="Частично обновляет день недели",
        tags=["Дни недели"]
    ),
    destroy=extend_schema(
        summary="Удалить день недели",
        description="Удаляет день недели",
        tags=["Дни недели"]
    ),
)
class DayViewSet(viewsets.ModelViewSet):
    """ViewSet для управления днями недели"""
    
    queryset = Day.objects.all()
    serializer_class = DaySerializer
    permission_classes = [IsAdminOrReadOnly]


@extend_schema_view(
    list=extend_schema(
        summary="Получить список типов предметов",
        description="Возвращает список всех типов предметов",
        tags=["Типы предметов"]
    ),
    retrieve=extend_schema(
        summary="Получить тип предмета",
        description="Возвращает информацию о типе предмета",
        tags=["Типы предметов"]
    ),
    create=extend_schema(
        summary="Создать тип предмета",
        description="Создает новый тип предмета",
        tags=["Типы предметов"]
    ),
    update=extend_schema(
        summary="Обновить тип предмета",
        description="Обновляет тип предмета",
        tags=["Типы предметов"]
    ),
    partial_update=extend_schema(
        summary="Частично обновить тип предмета",
        description="Частично обновляет тип предмета",
        tags=["Типы предметов"]
    ),
    destroy=extend_schema(
        summary="Удалить тип предмета",
        description="Удаляет тип предмета",
        tags=["Типы предметов"]
    ),
)
class SubjectsTypesViewSet(viewsets.ModelViewSet):
    """ViewSet для управления типами предметов"""
    
    queryset = SubjectsTypes.objects.all()
    serializer_class = SubjectsTypesSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ['title']
    ordering = ['title']


@extend_schema_view(
    list=extend_schema(
        summary="Получить список расписаний",
        description="""Возвращает список всех временных слотов расписания с полной информацией:
        - День недели и время занятия
        - Информация о предмете (название, тип)
        - Детали аудитории (номер, этаж, корпус)
        - Список групп (ID и названия)
        - Список преподавателей (ID, имя пользователя, ФИО)
        - Тип недели (Четные/Нечетные/Все)
        
        Поддерживает фильтрацию по:
        - subject: ID предмета
        - day: ID дня недели
        - time_slot: ID временного слота
        - week_type: тип недели (Четные/Нечетные/Все)
        - group: ID группы (для получения расписания конкретной группы)
        - teacher: ID преподавателя (для получения расписания преподавателя)
        """,
        tags=["Расписание"],
        parameters=[
            OpenApiParameter(name='subject', type=int, description='Фильтр по ID предмета'),
            OpenApiParameter(name='day', type=int, description='Фильтр по ID дня недели'),
            OpenApiParameter(name='time_slot', type=int, description='Фильтр по ID временного слота'),
            OpenApiParameter(name='week_type', type=str, description='Фильтр по типу недели (Четные/Нечетные/Все)'),
            OpenApiParameter(name='group', type=int, description='Фильтр по ID группы'),
            OpenApiParameter(name='teacher', type=int, description='Фильтр по ID преподавателя'),
        ]
    ),
    retrieve=extend_schema(
        summary="Получить расписание",
        description="""Возвращает детальную информацию о конкретном расписании, включая:
        - Полную информацию о дне недели и временном слоте
        - Детали о группах (ID, название, активность, количество студентов)
        - Детали о преподавателях (ID, username, ФИО, email)
        - Тип недели
        """,
        tags=["Расписание"]
    ),
    create=extend_schema(
        summary="Создать расписание",
        description="Создает новое расписание для предмета с привязкой к дню, времени, группам и преподавателям",
        tags=["Расписание"]
    ),
    update=extend_schema(
        summary="Обновить расписание",
        description="Обновляет расписание",
        tags=["Расписание"]
    ),
    partial_update=extend_schema(
        summary="Частично обновить расписание",
        description="Частично обновляет расписание",
        tags=["Расписание"]
    ),
    destroy=extend_schema(
        summary="Удалить расписание",
        description="Удаляет расписание",
        tags=["Расписание"]
    ),
)
class SubjectScheduleViewSet(viewsets.ModelViewSet):
    """ViewSet для управления расписанием предметов"""
    
    queryset = SubjectSchedule.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    ordering = ['week_day', 'time_slot__number']

    def get_serializer_class(self):
        if self.action == 'list':
            return SubjectScheduleListSerializer
        elif self.action == 'retrieve':
            return SubjectScheduleDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return SubjectScheduleCreateUpdateSerializer
        return SubjectScheduleDetailSerializer

    def get_queryset(self):
        queryset = SubjectSchedule.objects.select_related(
            'subject',
            'subject__subject_type',
            'subject__audience',
            'subject__audience__building',
            'week_day',
            'time_slot'
        ).prefetch_related(
            'teachers',
            'groups'
        )
        
        # Фильтрация по предмету
        subject_id = self.request.query_params.get('subject', None)
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        
        # Фильтрация по дню недели
        day_id = self.request.query_params.get('day', None)
        if day_id:
            queryset = queryset.filter(week_day_id=day_id)
        
        # Фильтрация по временному слоту
        time_slot_id = self.request.query_params.get('time_slot', None)
        if time_slot_id:
            queryset = queryset.filter(time_slot_id=time_slot_id)
        
        # Фильтрация по типу недели
        week_type = self.request.query_params.get('week_type', None)
        if week_type:
            queryset = queryset.filter(week_type=week_type)
        
        # Фильтрация по группе
        group_id = self.request.query_params.get('groups', None)
        if group_id:
            queryset = queryset.filter(groups__id=group_id)
        
        # Фильтрация по преподавателю
        teacher_id = self.request.query_params.get('teacher', None)
        if teacher_id:
            queryset = queryset.filter(teachers__id=teacher_id)
        
        return queryset.distinct()


@extend_schema_view(
    list=extend_schema(
        summary="Получить список предметов",
        description="Возвращает список всех предметов с возможностью фильтрации",
        tags=["Предметы"]
    ),
    retrieve=extend_schema(
        summary="Получить предмет",
        description="Возвращает детальную информацию о предмете",
        tags=["Предметы"]
    ),
    create=extend_schema(
        summary="Создать предмет",
        description="Создает новый предмет",
        tags=["Предметы"]
    ),
    update=extend_schema(
        summary="Обновить предмет",
        description="Обновляет предмет",
        tags=["Предметы"]
    ),
    partial_update=extend_schema(
        summary="Частично обновить предмет",
        description="Частично обновляет предмет",
        tags=["Предметы"]
    ),
    destroy=extend_schema(
        summary="Удалить предмет",
        description="Удаляет предмет",
        tags=["Предметы"]
    ),
)
class SubjectsViewSet(viewsets.ModelViewSet):
    """ViewSet для управления предметами"""
    
    queryset = Subjects.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    search_fields = ['title', 'subject_type__title']
    ordering_fields = ['title', 'subject_type__title']
    ordering = ['title']

    def get_serializer_class(self):
        print(self.action)
        if self.action == 'list':
            return SubjectsListSerializer
        elif self.action == 'retrieve':
            return SubjectsDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return SubjectsCreateUpdateSerializer
        return SubjectsDetailSerializer

    def get_queryset(self):
        try:
            queryset = Subjects.objects.select_related(
                'subject_type',
                'audience',
                'audience__building',
                'audience__auditorium_type'
            ).prefetch_related(
                'schedules__week_day',
                'schedules__time_slot',
                'schedules__teachers',
                'schedules__groups'
            )
            
            # Фильтрация по типу предмета
            subject_type_id = self.request.query_params.get('subject_type', None)
            if subject_type_id:
                queryset = queryset.filter(subject_type_id=subject_type_id)
            
            # Фильтрация по преподавателю
            teacher_id = self.request.query_params.get('teacher', None)
            if teacher_id:
                queryset = queryset.filter(teachers__id=teacher_id)
            
            # Фильтрация по группе
            group_id = self.request.query_params.get('group', None)
            if group_id:
                queryset = queryset.filter(groups__id=group_id)
            
            # Фильтрация по аудитории
            audience_id = self.request.query_params.get('audience', None)
            if audience_id:
                queryset = queryset.filter(audience_id=audience_id)
        except Exception as e:
            print(e)
            raise e
        return queryset.distinct()

    @extend_schema(
        summary="Получить расписание группы",
        description="Возвращает расписание занятий для конкретной группы",
        tags=["Предметы"],
        parameters=[
            OpenApiParameter(name='group_id', type=int, required=True, description='ID группы')
        ]
    )
    @action(detail=False, methods=['get'])
    def group_timetable(self, request):
        """Получить расписание для группы"""
        group_id = request.query_params.get('group_id')
        
        if not group_id:
            return Response(
                {'error': _('Необходимо указать group_id')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Теперь фильтруем по SubjectSchedule
        schedules = SubjectSchedule.objects.filter(groups__id=group_id).select_related(
            'subject', 'subject__subject_type', 'subject__audience', 'week_day', 'time_slot'
        ).prefetch_related('teachers', 'groups')
        
        timetable = []
        for schedule_item in schedules:
            timetable.append({
                'day': schedule_item.week_day.title,
                'time_slot': str(schedule_item.time_slot),
                'subject': schedule_item.subject.title,
                'subject_type': schedule_item.subject.subject_type.title,
                'audience': schedule_item.subject.audience.title,
                'teachers': [f"{t.last_name} {t.first_name}" if t.first_name else t.username for t in schedule_item.teachers.all()],
                'groups': [g.title for g in schedule_item.groups.all()],
                'week_type': schedule_item.week_type,
            })
        
        serializer = TimetableSerializer(timetable, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Получить расписание преподавателя",
        description="Возвращает расписание занятий для конкретного преподавателя",
        tags=["Предметы"],
        parameters=[
            OpenApiParameter(name='teacher_id', type=int, required=True, description='ID преподавателя')
        ]
    )
    @action(detail=False, methods=['get'])
    def teacher_timetable(self, request):
        """Получить расписание для преподавателя"""
        teacher_id = request.query_params.get('teacher_id')
        
        if not teacher_id:
            return Response(
                {'error': _('Необходимо указать teacher_id')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Теперь фильтруем по SubjectSchedule
        schedules = SubjectSchedule.objects.filter(teachers__id=teacher_id).select_related(
            'subject', 'subject__subject_type', 'subject__audience', 'week_day', 'time_slot'
        ).prefetch_related('teachers', 'groups')
        
        timetable = []
        for schedule_item in schedules:
            timetable.append({
                'day': schedule_item.week_day.title,
                'time_slot': str(schedule_item.time_slot),
                'subject': schedule_item.subject.title,
                'subject_type': schedule_item.subject.subject_type.title,
                'audience': schedule_item.subject.audience.title,
                'teachers': [f"{t.last_name} {t.first_name}" if t.first_name else t.username for t in schedule_item.teachers.all()],
                'groups': [g.title for g in schedule_item.groups.all()],
                'week_type': schedule_item.week_type,
            })
        
        serializer = TimetableSerializer(timetable, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Получить расписание аудитории",
        description="Возвращает расписание занятий для конкретной аудитории",
        tags=["Предметы"],
        parameters=[
            OpenApiParameter(name='audience_id', type=int, required=True, description='ID аудитории')
        ]
    )
    @action(detail=False, methods=['get'])
    def audience_timetable(self, request):
        """Получить расписание для аудитории"""
        audience_id = request.query_params.get('audience_id')
        
        if not audience_id:
            return Response(
                {'error': _('Необходимо указать audience_id')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        schedules = SubjectSchedule.objects.filter(subject__audience_id=audience_id).select_related(
            'subject', 'subject__subject_type', 'subject__audience', 'week_day', 'time_slot'
        ).prefetch_related('teachers', 'groups')
        
        timetable = []
        for schedule_item in schedules:
            timetable.append({
                'day': schedule_item.week_day.title,
                'time_slot': str(schedule_item.time_slot),
                'subject': schedule_item.subject.title,
                'subject_type': schedule_item.subject.subject_type.title,
                'audience': schedule_item.subject.audience.title,
                'teachers': [f"{t.last_name} {t.first_name}" if t.first_name else t.username for t in schedule_item.teachers.all()],
                'groups': [g.title for g in schedule_item.groups.all()],
                'week_type': schedule_item.week_type,
            })
        
        serializer = TimetableSerializer(timetable, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Экспорт расписания группы в PDF",
        description="Экспортирует расписание учебной группы в формате PDF",
        tags=["Предметы"],
        parameters=[
            OpenApiParameter(name='group_id', type=int, required=True, description='ID группы')
        ]
    )
    @action(detail=False, methods=['get'])
    def export_group_pdf(self, request):
        """Экспорт расписания группы в PDF"""
        group_id = request.query_params.get('group_id')
        
        if not group_id:
            return Response(
                {'error': _('Необходимо указать group_id')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        schedules = SubjectSchedule.objects.filter(groups__id=group_id).select_related(
            'subject', 'subject__subject_type', 'subject__audience', 'week_day', 'time_slot'
        ).prefetch_related('teachers', 'groups')
        
        timetable = []
        for schedule_item in schedules:
            timetable.append({
                'day': schedule_item.week_day.title,
                'time_slot': str(schedule_item.time_slot),
                'subject': schedule_item.subject.title,
                'subject_type': schedule_item.subject.subject_type.title,
                'audience': schedule_item.subject.audience.title,
                'teachers': [f"{t.last_name} {t.first_name}" if t.first_name else t.username for t in schedule_item.teachers.all()],
                'groups': [g.title for g in schedule_item.groups.all()],
                'week_type': schedule_item.week_type,
            })
        
        return generate_pdf_timetable(timetable, f"Расписание группы {group_id}")

    @extend_schema(
        summary="Экспорт расписания группы в Excel",
        description="Экспортирует расписание учебной группы в формате Excel",
        tags=["Предметы"],
        parameters=[
            OpenApiParameter(name='group_id', type=int, required=True, description='ID группы')
        ]
    )
    @action(detail=False, methods=['get'])
    def export_group_excel(self, request):
        """Экспорт расписания группы в Excel"""
        group_id = request.query_params.get('group_id')
        
        if not group_id:
            return Response(
                {'error': _('Необходимо указать group_id')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        schedules = SubjectSchedule.objects.filter(groups__id=group_id).select_related(
            'subject', 'subject__subject_type', 'subject__audience', 'week_day', 'time_slot'
        ).prefetch_related('teachers', 'groups')
        
        timetable = []
        for schedule_item in schedules:
            timetable.append({
                'day': schedule_item.week_day.title,
                'time_slot': str(schedule_item.time_slot),
                'subject': schedule_item.subject.title,
                'subject_type': schedule_item.subject.subject_type.title,
                'audience': schedule_item.subject.audience.title,
                'teachers': [f"{t.last_name} {t.first_name}" if t.first_name else t.username for t in schedule_item.teachers.all()],
                'groups': [g.title for g in schedule_item.groups.all()],
                'week_type': schedule_item.week_type,
            })
        
        return generate_excel_timetable(timetable, f"Расписание группы {group_id}")

    @extend_schema(
        summary="Экспорт расписания преподавателя в PDF",
        description="Экспортирует расписание преподавателя в формате PDF",
        tags=["Предметы"],
        parameters=[
            OpenApiParameter(name='teacher_id', type=int, required=True, description='ID преподавателя')
        ]
    )
    @action(detail=False, methods=['get'])
    def export_teacher_pdf(self, request):
        """Экспорт расписания преподавателя в PDF"""
        teacher_id = request.query_params.get('teacher_id')
        
        if not teacher_id:
            return Response(
                {'error': _('Необходимо указать teacher_id')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        schedules = SubjectSchedule.objects.filter(teachers__id=teacher_id).select_related(
            'subject', 'subject__subject_type', 'subject__audience', 'week_day', 'time_slot'
        ).prefetch_related('teachers', 'groups')
        
        timetable = []
        for schedule_item in schedules:
            timetable.append({
                'day': schedule_item.week_day.title,
                'time_slot': str(schedule_item.time_slot),
                'subject': schedule_item.subject.title,
                'subject_type': schedule_item.subject.subject_type.title,
                'audience': schedule_item.subject.audience.title,
                'teachers': [f"{t.last_name} {t.first_name}" if t.first_name else t.username for t in schedule_item.teachers.all()],
                'groups': [g.title for g in schedule_item.groups.all()],
                'week_type': schedule_item.week_type,
            })
        
        return generate_pdf_timetable(timetable, f"Расписание преподавателя {teacher_id}")

    @extend_schema(
        summary="Экспорт расписания преподавателя в Excel",
        description="Экспортирует расписание преподавателя в формате Excel",
        tags=["Предметы"],
        parameters=[
            OpenApiParameter(name='teacher_id', type=int, required=True, description='ID преподавателя')
        ]
    )
    @action(detail=False, methods=['get'])
    def export_teacher_excel(self, request):
        """Экспорт расписания преподавателя в Excel"""
        teacher_id = request.query_params.get('teacher_id')
        
        if not teacher_id:
            return Response(
                {'error': _('Необходимо указать teacher_id')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        schedules = SubjectSchedule.objects.filter(teachers__id=teacher_id).select_related(
            'subject', 'subject__subject_type', 'subject__audience', 'week_day', 'time_slot'
        ).prefetch_related('teachers', 'groups')
        
        timetable = []
        for schedule_item in schedules:
            timetable.append({
                'day': schedule_item.week_day.title,
                'time_slot': str(schedule_item.time_slot),
                'subject': schedule_item.subject.title,
                'subject_type': schedule_item.subject.subject_type.title,
                'audience': schedule_item.subject.audience.title,
                'teachers': [f"{t.last_name} {t.first_name}" if t.first_name else t.username for t in schedule_item.teachers.all()],
                'groups': [g.title for g in schedule_item.groups.all()],
                'week_type': schedule_item.week_type,
            })
        
        return generate_excel_timetable(timetable, f"Расписание преподавателя {teacher_id}")


@extend_schema_view(
    list=extend_schema(
        summary="Получить список переопределений расписания",
        description="Возвращает список всех переопределений расписания с возможностью фильтрации",
        tags=["Переопределения расписания"]
    ),
    retrieve=extend_schema(
        summary="Получить переопределение расписания",
        description="Возвращает детальную информацию о переопределении расписания",
        tags=["Переопределения расписания"]
    ),
    create=extend_schema(
        summary="Создать переопределение расписания",
        description="Создает новое переопределение расписания (отмена или перенос занятия)",
        tags=["Переопределения расписания"]
    ),
    update=extend_schema(
        summary="Обновить переопределение расписания",
        description="Обновляет переопределение расписания",
        tags=["Переопределения расписания"]
    ),
    partial_update=extend_schema(
        summary="Частично обновить переопределение расписания",
        description="Частично обновляет переопределение расписания",
        tags=["Переопределения расписания"]
    ),
    destroy=extend_schema(
        summary="Удалить переопределение расписания",
        description="Удаляет переопределение расписания",
        tags=["Переопределения расписания"]
    ),
)
class ScheduleGeneratorViewSet(viewsets.ViewSet):
    """ViewSet для автоматической генерации расписания"""
    
    def get_permissions(self):
        """Разные права для разных действий"""
        if self.action == 'time_ranges':
            # Список временных промежутков доступен всем
            return []
        return [IsAuthenticated()]
    
    @extend_schema(
        summary="Сгенерировать расписание",
        description=(
            "Автоматически генерирует расписание для указанных групп.\n\n"
            "**Алгоритм учитывает:**\n"
            "- У одной группы не может быть более одного предмета в одно время\n"
            "- В одной аудитории не может быть более одного предмета (кроме потоковых)\n"
            "- Преподаватель не может вести несколько предметов одновременно\n"
            "- Поддержка потоковых предметов (один предмет для нескольких групп)\n\n"
            "**Временные промежутки:**\n"
            "- `morning`: Утренние пары (08:00-14:30)\n"
            "- `mixed`: Смешанные пары (11:30-17:00)\n"
            "- `afternoon`: Послеобеденные пары (13:00-18:20)\n"
            "- `evening`: Вечерние пары (16:00-21:00)\n"
            "- `full`: Весь день (08:00-21:00)\n"
            "- Или укажите `custom_start_time` и `custom_end_time` в формате HH:MM"
        ),
        request=ScheduleGenerationRequestSerializer,
        responses={
            200: ScheduleGenerationResponseSerializer,
            400: ScheduleGenerationResponseSerializer,
        },
        tags=["Генерация расписания"]
    )
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Генерация расписания для групп"""
        serializer = ScheduleGenerationRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'success': False, 'messages': [str(serializer.errors)], 'statistics': {}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        group_id = serializer.validated_data['group_id']
        subject_ids = serializer.validated_data['subject_ids']
        clear_existing = serializer.validated_data.get('clear_existing', False)
        prefer_morning = serializer.validated_data.get('prefer_morning', True)
        time_range = serializer.validated_data.get('time_range')
        custom_start_time = serializer.validated_data.get('custom_start_time')
        custom_end_time = serializer.validated_data.get('custom_end_time')
        start_day_id = serializer.validated_data.get('start_day_id')
        end_day_id = serializer.validated_data.get('end_day_id')
        
        success, messages, statistics = generate_schedule_for_group(
            group_id=group_id,
            subject_ids=subject_ids,
            clear_existing=clear_existing,
            prefer_morning=prefer_morning,
            time_range=time_range,
            custom_start_time=custom_start_time,
            custom_end_time=custom_end_time,
            start_day_id=start_day_id,
            end_day_id=end_day_id
        )
        
        response_data = {
            'success': success,
            'messages': messages,
            'statistics': statistics
        }
        
        response_serializer = ScheduleGenerationResponseSerializer(response_data)
        
        if success:
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(response_serializer.data, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="Валидировать расписание",
        description=(
            "Проверяет расписание групп на наличие конфликтов:\n"
            "- Конфликты групп (два предмета одновременно)\n"
            "- Конфликты аудиторий (занята несколькими предметами)\n"
            "- Конфликты преподавателей (ведет несколько предметов одновременно)"
        ),
        parameters=[
            OpenApiParameter(
                name='group_ids',
                type={'type': 'array', 'items': {'type': 'integer'}},
                location=OpenApiParameter.QUERY,
                required=True,
                description='Список ID групп для проверки (через запятую)',
                style='form',
                explode=False
            )
        ],
        responses={200: ScheduleValidationResponseSerializer},
        tags=["Генерация расписания"]
    )
    @action(detail=False, methods=['get'])
    def validate(self, request):
        """Валидация расписания на наличие конфликтов"""
        group_ids_str = request.query_params.get('group_ids', '')
        
        if not group_ids_str:
            return Response(
                {
                    'is_valid': False,
                    'conflicts': [_('Необходимо указать group_ids')]
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            group_ids = [int(id) for id in group_ids_str.split(',')]
        except ValueError:
            return Response(
                {
                    'is_valid': False,
                    'conflicts': [_('Некорректный формат group_ids')]
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        is_valid, conflicts = validate_generated_schedule(group_ids)
        
        response_data = {
            'is_valid': is_valid,
            'conflicts': conflicts
        }
        
        serializer = ScheduleValidationResponseSerializer(response_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        summary="Статистика расписания",
        description="Возвращает статистику по расписанию указанных групп",
        parameters=[
            OpenApiParameter(
                name='group_ids',
                type={'type': 'array', 'items': {'type': 'integer'}},
                location=OpenApiParameter.QUERY,
                required=True,
                description='Список ID групп (через запятую)',
                style='form',
                explode=False
            )
        ],
        responses={200: ScheduleStatisticsSerializer},
        tags=["Генерация расписания"]
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Статистика расписания групп"""
        group_ids_str = request.query_params.get('group_ids', '')
        
        if not group_ids_str:
            return Response(
                {'error': _('Необходимо указать group_ids')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            group_ids = [int(id) for id in group_ids_str.split(',')]
        except ValueError:
            return Response(
                {'error': _('Некорректный формат group_ids')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        stats = get_schedule_statistics(group_ids)
        serializer = ScheduleStatisticsSerializer(stats)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        summary="Получить доступные временные промежутки",
        description="Возвращает список предустановленных временных промежутков для генерации расписания",
        responses={200: AvailableTimeRangesSerializer},
        tags=["Генерация расписания"]
    )
    @action(detail=False, methods=['get'])
    def time_ranges(self, request):
        """Получить список доступных временных промежутков"""
        ranges = get_available_time_ranges()
        serializer = AvailableTimeRangesSerializer(ranges)
        return Response(serializer.data, status=status.HTTP_200_OK)
