from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.users.permissions import IsAdminOrReadOnly

from .models import StudyGroups
from .serializers import (
    StudyGroupsListSerializer,
    StudyGroupsDetailSerializer,
    StudyGroupsCreateUpdateSerializer,
    AddStudentsSerializer,
    RemoveStudentsSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary="Получить список учебных групп",
        description="Возвращает список всех учебных групп с возможностью фильтрации",
        tags=["Учебные группы"]
    ),
    retrieve=extend_schema(
        summary="Получить учебную группу",
        description="Возвращает детальную информацию об учебной группе со списком студентов",
        tags=["Учебные группы"]
    ),
    create=extend_schema(
        summary="Создать учебную группу",
        description="Создает новую учебную группу",
        tags=["Учебные группы"]
    ),
    update=extend_schema(
        summary="Обновить учебную группу",
        description="Обновляет всю информацию об учебной группе",
        tags=["Учебные группы"]
    ),
    partial_update=extend_schema(
        summary="Частично обновить учебную группу",
        description="Частично обновляет информацию об учебной группе",
        tags=["Учебные группы"]
    ),
    destroy=extend_schema(
        summary="Удалить учебную группу",
        description="Удаляет учебную группу из системы",
        tags=["Учебные группы"]
    ),
)
class StudyGroupsViewSet(viewsets.ModelViewSet):
    """ViewSet для управления учебными группами"""
    
    queryset = StudyGroups.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ['title', 'description', 'faculty']
    filterset_fields = ['faculty', 'course', 'is_active']
    ordering_fields = ['title', 'faculty', 'course', 'is_active']
    ordering = ['title']

    def get_serializer_class(self):
        if self.action == 'list':
            return StudyGroupsListSerializer
        elif self.action == 'retrieve':
            return StudyGroupsDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return StudyGroupsCreateUpdateSerializer
        elif self.action == 'add_students':
            return AddStudentsSerializer
        elif self.action == 'remove_students':
            return RemoveStudentsSerializer
        return StudyGroupsDetailSerializer

    def get_queryset(self):
        queryset = StudyGroups.objects.prefetch_related('students')
        
        # Фильтрация по статусу активности
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active_bool = is_active.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_active=is_active_bool)
        
        # Фильтрация по студенту (группы в которых состоит студент)
        student_id = self.request.query_params.get('student_id', None)
        if student_id:
            queryset = queryset.filter(students__id=student_id)
        
        return queryset

    @extend_schema(
        summary="Добавить студентов в группу",
        description="Добавляет одного или нескольких студентов в учебную группу",
        request=AddStudentsSerializer,
        tags=["Учебные группы"]
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_students(self, request, pk=None):
        """Добавить студентов в группу"""
        study_group = self.get_object()
        serializer = AddStudentsSerializer(data=request.data)
        
        if serializer.is_valid():
            student_ids = serializer.validated_data['student_ids']
            
            # Добавляем студентов в группу
            for student in student_ids:
                if student not in study_group.students.all():
                    study_group.students.add(student)
            
            return Response({
                'detail': _('Студенты успешно добавлены в группу.'),
                'added_count': len(student_ids),
                'total_students': study_group.students.count()
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Удалить студентов из группы",
        description="Удаляет одного или нескольких студентов из учебной группы",
        request=RemoveStudentsSerializer,
        tags=["Учебные группы"]
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def remove_students(self, request, pk=None):
        """Удалить студентов из группы"""
        study_group = self.get_object()
        serializer = RemoveStudentsSerializer(data=request.data)
        
        if serializer.is_valid():
            student_ids = serializer.validated_data['student_ids']
            
            # Удаляем студентов из группы
            removed_count = 0
            for student in student_ids:
                if student in study_group.students.all():
                    study_group.students.remove(student)
                    removed_count += 1
            
            return Response({
                'detail': _('Студенты успешно удалены из группы.'),
                'removed_count': removed_count,
                'total_students': study_group.students.count()
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Получить список студентов группы",
        description="Возвращает список всех студентов учебной группы",
        tags=["Учебные группы"]
    )
    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        """Получить список студентов группы"""
        study_group = self.get_object()
        students = study_group.students.all()
        
        from apps.users.serializers import StudentSerializer
        serializer = StudentSerializer(students, many=True)
        
        return Response({
            'group': study_group.title,
            'students_count': students.count(),
            'students': serializer.data
        })

    @extend_schema(
        summary="Статистика по группе",
        description="Возвращает статистику: количество студентов, активность группы",
        tags=["Учебные группы"]
    )
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Получить статистику по группе"""
        study_group = self.get_object()
        students = study_group.students.all()
        
        # Подсчет по полу
        gender_stats = {
            'male': students.filter(gender='M').count(),
            'female': students.filter(gender='F').count(),
            'not_specified': students.filter(gender='N').count(),
        }
        
        return Response({
            'group': study_group.title,
            'is_active': study_group.is_active,
            'total_students': students.count(),
            'gender_distribution': gender_stats,
        })

    @extend_schema(
        summary="Активировать/деактивировать группу",
        description="Изменяет статус активности учебной группы",
        tags=["Учебные группы"]
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def toggle_active(self, request, pk=None):
        """Активировать/деактивировать группу"""
        study_group = self.get_object()
        study_group.is_active = not study_group.is_active
        study_group.save()
        
        status_text = _('активирована') if study_group.is_active else _('деактивирована')
        
        return Response({
            'detail': _('Группа {status}.').format(status=status_text),
            'is_active': study_group.is_active
        }, status=status.HTTP_200_OK)
