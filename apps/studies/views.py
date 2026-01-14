from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.utils.translation import gettext_lazy as _
from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from apps.users.permissions import IsAdminOrReadOnly

from .models import TimeSlot, Day, SubjectsTypes, Schedule, Subjects, ScheduleOverride
from .serializers import (
    TimeSlotSerializer,
    DaySerializer,
    SubjectsTypesSerializer,
    ScheduleListSerializer,
    ScheduleDetailSerializer,
    ScheduleCreateUpdateSerializer,
    SubjectsListSerializer,
    SubjectsDetailSerializer,
    SubjectsCreateUpdateSerializer,
    TimetableSerializer,
    ScheduleOverrideSerializer,
    ScheduleOverrideCreateUpdateSerializer,
)
from .export_utils import generate_pdf_timetable, generate_excel_timetable


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
        description="Возвращает список всех временных слотов расписания",
        tags=["Расписание"]
    ),
    retrieve=extend_schema(
        summary="Получить расписание",
        description="Возвращает детальную информацию о расписании",
        tags=["Расписание"]
    ),
    create=extend_schema(
        summary="Создать расписание",
        description="Создает новое расписание",
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
class ScheduleViewSet(viewsets.ModelViewSet):
    """ViewSet для управления расписанием"""
    
    queryset = Schedule.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    ordering = ['week_day', 'time_slot__number']

    def get_serializer_class(self):
        if self.action == 'list':
            return ScheduleListSerializer
        elif self.action == 'retrieve':
            return ScheduleDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ScheduleCreateUpdateSerializer
        return ScheduleDetailSerializer

    def get_queryset(self):
        queryset = Schedule.objects.select_related('week_day', 'time_slot')
        
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
        
        return queryset


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
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ['title', 'subject_type__title']
    ordering_fields = ['title', 'subject_type__title']
    ordering = ['title']

    def get_serializer_class(self):
        if self.action == 'list':
            return SubjectsListSerializer
        elif self.action == 'retrieve':
            return SubjectsDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return SubjectsCreateUpdateSerializer
        return SubjectsDetailSerializer

    def get_queryset(self):
        queryset = Subjects.objects.select_related(
            'subject_type',
            'audience',
            'audience__building',
            'audience__auditorium_type'
        ).prefetch_related(
            'schedule__week_day',
            'schedule__time_slot',
            'teachers',
            'groups'
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
        
        subjects = self.get_queryset().filter(groups__id=group_id)
        
        timetable = []
        for subject in subjects:
            for schedule_item in subject.schedule.all():
                timetable.append({
                    'day': schedule_item.week_day.title,
                    'time_slot': str(schedule_item.time_slot),
                    'subject': subject.title,
                    'subject_type': subject.subject_type.title,
                    'audience': subject.audience.title,
                    'teachers': [f"{t.last_name} {t.first_name}" if t.first_name else t.username for t in subject.teachers.all()],
                    'groups': [g.title for g in subject.groups.all()],
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
        
        subjects = self.get_queryset().filter(teachers__id=teacher_id)
        
        timetable = []
        for subject in subjects:
            for schedule_item in subject.schedule.all():
                timetable.append({
                    'day': schedule_item.week_day.title,
                    'time_slot': str(schedule_item.time_slot),
                    'subject': subject.title,
                    'subject_type': subject.subject_type.title,
                    'audience': subject.audience.title,
                    'teachers': [f"{t.last_name} {t.first_name}" if t.first_name else t.username for t in subject.teachers.all()],
                    'groups': [g.title for g in subject.groups.all()],
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
        
        subjects = self.get_queryset().filter(audience_id=audience_id)
        
        timetable = []
        for subject in subjects:
            for schedule_item in subject.schedule.all():
                timetable.append({
                    'day': schedule_item.week_day.title,
                    'time_slot': str(schedule_item.time_slot),
                    'subject': subject.title,
                    'subject_type': subject.subject_type.title,
                    'audience': subject.audience.title,
                    'teachers': [f"{t.last_name} {t.first_name}" if t.first_name else t.username for t in subject.teachers.all()],
                    'groups': [g.title for g in subject.groups.all()],
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
        
        subjects = self.get_queryset().filter(groups__id=group_id)
        
        timetable = []
        for subject in subjects:
            for schedule_item in subject.schedule.all():
                timetable.append({
                    'day': schedule_item.week_day.title,
                    'time_slot': str(schedule_item.time_slot),
                    'subject': subject.title,
                    'subject_type': subject.subject_type.title,
                    'audience': subject.audience.title,
                    'teachers': [f"{t.last_name} {t.first_name}" if t.first_name else t.username for t in subject.teachers.all()],
                    'groups': [g.title for g in subject.groups.all()],
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
        
        subjects = self.get_queryset().filter(groups__id=group_id)
        
        timetable = []
        for subject in subjects:
            for schedule_item in subject.schedule.all():
                timetable.append({
                    'day': schedule_item.week_day.title,
                    'time_slot': str(schedule_item.time_slot),
                    'subject': subject.title,
                    'subject_type': subject.subject_type.title,
                    'audience': subject.audience.title,
                    'teachers': [f"{t.last_name} {t.first_name}" if t.first_name else t.username for t in subject.teachers.all()],
                    'groups': [g.title for g in subject.groups.all()],
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
        
        subjects = self.get_queryset().filter(teachers__id=teacher_id)
        
        timetable = []
        for subject in subjects:
            for schedule_item in subject.schedule.all():
                timetable.append({
                    'day': schedule_item.week_day.title,
                    'time_slot': str(schedule_item.time_slot),
                    'subject': subject.title,
                    'subject_type': subject.subject_type.title,
                    'audience': subject.audience.title,
                    'teachers': [f"{t.last_name} {t.first_name}" if t.first_name else t.username for t in subject.teachers.all()],
                    'groups': [g.title for g in subject.groups.all()],
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
        
        subjects = self.get_queryset().filter(teachers__id=teacher_id)
        
        timetable = []
        for subject in subjects:
            for schedule_item in subject.schedule.all():
                timetable.append({
                    'day': schedule_item.week_day.title,
                    'time_slot': str(schedule_item.time_slot),
                    'subject': subject.title,
                    'subject_type': subject.subject_type.title,
                    'audience': subject.audience.title,
                    'teachers': [f"{t.last_name} {t.first_name}" if t.first_name else t.username for t in subject.teachers.all()],
                    'groups': [g.title for g in subject.groups.all()],
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
class ScheduleOverrideViewSet(viewsets.ModelViewSet):
    """ViewSet для управления переопределениями расписания"""
    
    queryset = ScheduleOverride.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    ordering = ['-date', 'time_slot__number']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ScheduleOverrideCreateUpdateSerializer
        return ScheduleOverrideSerializer

    def get_queryset(self):
        queryset = ScheduleOverride.objects.select_related(
            'subject',
            'time_slot',
            'audience'
        )
        
        # Фильтрация по предмету
        subject_id = self.request.query_params.get('subject_id', None)
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        
        # Фильтрация по дате
        date = self.request.query_params.get('date', None)
        if date:
            queryset = queryset.filter(date=date)
        
        # Фильтрация по диапазону дат
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        # Фильтрация по статусу отмены
        is_cancelled = self.request.query_params.get('is_cancelled', None)
        if is_cancelled is not None:
            is_cancelled_bool = is_cancelled.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_cancelled=is_cancelled_bool)
        
        return queryset
