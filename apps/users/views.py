from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    StudentSerializer,
    TeacherSerializer,
)
from .choices import RoleChoices
from .permissions import IsAdminOrOwner, IsAdmin

User = get_user_model()


@extend_schema_view(
    list=extend_schema(
        summary="Получить список пользователей",
        description="Возвращает список всех пользователей системы",
        tags=["Пользователи"]
    ),
    retrieve=extend_schema(
        summary="Получить пользователя",
        description="Возвращает информацию о конкретном пользователе",
        tags=["Пользователи"]
    ),
    create=extend_schema(
        summary="Создать пользователя",
        description="Создает нового пользователя в системе",
        tags=["Пользователи"]
    ),
    update=extend_schema(
        summary="Обновить пользователя",
        description="Обновляет информацию о пользователе",
        tags=["Пользователи"]
    ),
    partial_update=extend_schema(
        summary="Частично обновить пользователя",
        description="Частично обновляет информацию о пользователе",
        tags=["Пользователи"]
    ),
    destroy=extend_schema(
        summary="Удалить пользователя",
        description="Удаляет пользователя из системы",
        tags=["Пользователи"]
    ),
)
class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для управления пользователями"""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'email', 'date_joined']
    ordering = ['-date_joined']

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAdminOrOwner()]
        elif self.action == 'list':
            return [IsAdmin()]
        return [IsAuthenticated()]

    @extend_schema(
        summary="Получить текущего пользователя",
        description="Возвращает информацию о текущем авторизованном пользователе",
        tags=["Пользователи"]
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Получить информацию о текущем пользователе"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        summary="Изменить пароль",
        description="Позволяет пользователю изменить свой пароль",
        request=ChangePasswordSerializer,
        tags=["Пользователи"]
    )
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Изменить пароль текущего пользователя"""
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"detail": _("Пароль успешно изменен.")},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        summary="Получить список студентов",
        description="Возвращает список всех студентов",
        tags=["Студенты"]
    ),
    retrieve=extend_schema(
        summary="Получить студента",
        description="Возвращает информацию о конкретном студенте",
        tags=["Студенты"]
    ),
)
class StudentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для просмотра студентов"""
    
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['last_name', 'first_name']

    def get_queryset(self):
        return User.objects.filter(role=RoleChoices.STUDENT)

    @extend_schema(
        summary="Получить группы студента",
        description="Возвращает список учебных групп, в которых состоит студент",
        tags=["Студенты"]
    )
    @action(detail=True, methods=['get'])
    def study_groups(self, request, pk=None):
        """Получить учебные группы студента"""
        student = self.get_object()
        groups = student.study_groups.all()
        from apps.groups.models import StudyGroups
        from rest_framework import serializers
        
        class SimpleGroupSerializer(serializers.ModelSerializer):
            class Meta:
                model = StudyGroups
                fields = ['id', 'title', 'description', 'is_active']
        
        serializer = SimpleGroupSerializer(groups, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="Получить список преподавателей",
        description="Возвращает список всех преподавателей",
        tags=["Преподаватели"]
    ),
    retrieve=extend_schema(
        summary="Получить преподавателя",
        description="Возвращает информацию о конкретном преподавателе",
        tags=["Преподаватели"]
    ),
)
class TeacherViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для просмотра преподавателей"""
    
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['last_name', 'first_name']

    def get_queryset(self):
        return User.objects.filter(role=RoleChoices.TEACHER)
