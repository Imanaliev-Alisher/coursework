from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from apps.users.permissions import IsAdminOrReadOnly

from .models import Buildings, Audiences, AudiencesTypes
from .serializers import (
    BuildingsListSerializer,
    BuildingsDetailSerializer,
    BuildingsCreateUpdateSerializer,
    AudiencesListSerializer,
    AudiencesDetailSerializer,
    AudiencesCreateUpdateSerializer,
    AudiencesTypesSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary="Получить список зданий",
        description="Возвращает список всех зданий с краткой информацией",
        tags=["Здания"]
    ),
    retrieve=extend_schema(
        summary="Получить здание",
        description="Возвращает детальную информацию о здании включая список аудиторий",
        tags=["Здания"]
    ),
    create=extend_schema(
        summary="Создать здание",
        description="Создает новое здание в системе",
        tags=["Здания"]
    ),
    update=extend_schema(
        summary="Обновить здание",
        description="Обновляет всю информацию о здании",
        tags=["Здания"]
    ),
    partial_update=extend_schema(
        summary="Частично обновить здание",
        description="Частично обновляет информацию о здании",
        tags=["Здания"]
    ),
    destroy=extend_schema(
        summary="Удалить здание",
        description="Удаляет здание из системы",
        tags=["Здания"]
    ),
)
class BuildingsViewSet(viewsets.ModelViewSet):
    """ViewSet для управления зданиями"""
    
    queryset = Buildings.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ['title', 'city', 'street', 'address']
    ordering_fields = ['title', 'city']
    ordering = ['title']

    def get_serializer_class(self):
        if self.action == 'list':
            return BuildingsListSerializer
        elif self.action == 'retrieve':
            return BuildingsDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return BuildingsCreateUpdateSerializer
        return BuildingsDetailSerializer

    def get_queryset(self):
        queryset = Buildings.objects.prefetch_related('audiences')
        
        # Фильтрация по городу
        city = self.request.query_params.get('city', None)
        if city:
            queryset = queryset.filter(city__icontains=city)
        
        # Фильтрация по стране
        country = self.request.query_params.get('country', None)
        if country:
            queryset = queryset.filter(country=country)
        
        return queryset

    @extend_schema(
        summary="Получить аудитории здания",
        description="Возвращает список всех аудиторий конкретного здания",
        tags=["Здания"],
        responses={200: AudiencesListSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def audiences(self, request, pk=None):
        """Получить список аудиторий здания"""
        building = self.get_object()
        audiences = building.audiences.select_related('auditorium_type')
        serializer = AudiencesListSerializer(audiences, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Статистика по зданию",
        description="Возвращает статистику: количество аудиторий, распределение по этажам и типам",
        tags=["Здания"]
    )
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Получить статистику по зданию"""
        building = self.get_object()
        audiences = building.audiences.all()
        
        # Группировка по этажам
        floors_stats = {}
        for audience in audiences:
            floor = audience.floor_number
            if floor not in floors_stats:
                floors_stats[floor] = 0
            floors_stats[floor] += 1
        
        # Группировка по типам
        types_stats = {}
        for audience in audiences:
            type_name = audience.auditorium_type.title
            if type_name not in types_stats:
                types_stats[type_name] = 0
            types_stats[type_name] += 1
        
        return Response({
            'building': building.title,
            'total_audiences': audiences.count(),
            'floors_distribution': floors_stats,
            'types_distribution': types_stats,
        })


@extend_schema_view(
    list=extend_schema(
        summary="Получить список аудиторий",
        description="Возвращает список всех аудиторий с возможностью фильтрации",
        tags=["Аудитории"]
    ),
    retrieve=extend_schema(
        summary="Получить аудиторию",
        description="Возвращает детальную информацию об аудитории",
        tags=["Аудитории"]
    ),
    create=extend_schema(
        summary="Создать аудиторию",
        description="Создает новую аудиторию в системе",
        tags=["Аудитории"]
    ),
    update=extend_schema(
        summary="Обновить аудиторию",
        description="Обновляет всю информацию об аудитории",
        tags=["Аудитории"]
    ),
    partial_update=extend_schema(
        summary="Частично обновить аудиторию",
        description="Частично обновляет информацию об аудитории",
        tags=["Аудитории"]
    ),
    destroy=extend_schema(
        summary="Удалить аудиторию",
        description="Удаляет аудиторию из системы",
        tags=["Аудитории"]
    ),
)
class AudiencesViewSet(viewsets.ModelViewSet):
    """ViewSet для управления аудиториями"""
    
    queryset = Audiences.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ['title', 'auditorium_number', 'building__title']
    ordering_fields = ['auditorium_number', 'floor_number', 'building__title']
    ordering = ['building__title', 'floor_number', 'auditorium_number']

    def get_serializer_class(self):
        if self.action == 'list':
            return AudiencesListSerializer
        elif self.action == 'retrieve':
            return AudiencesDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return AudiencesCreateUpdateSerializer
        return AudiencesDetailSerializer

    def get_queryset(self):
        queryset = Audiences.objects.select_related(
            'building',
            'auditorium_type'
        )
        
        # Фильтрация по зданию
        building_id = self.request.query_params.get('building', None)
        if building_id:
            queryset = queryset.filter(building_id=building_id)
        
        # Фильтрация по этажу
        floor = self.request.query_params.get('floor', None)
        if floor:
            queryset = queryset.filter(floor_number=floor)
        
        # Фильтрация по типу
        audience_type_id = self.request.query_params.get('type', None)
        if audience_type_id:
            queryset = queryset.filter(auditorium_type_id=audience_type_id)
        
        return queryset


@extend_schema_view(
    list=extend_schema(
        summary="Получить список типов аудиторий",
        description="Возвращает список всех типов аудиторий",
        tags=["Типы аудиторий"]
    ),
    retrieve=extend_schema(
        summary="Получить тип аудитории",
        description="Возвращает информацию о типе аудитории",
        tags=["Типы аудиторий"]
    ),
    create=extend_schema(
        summary="Создать тип аудитории",
        description="Создает новый тип аудитории",
        tags=["Типы аудиторий"]
    ),
    update=extend_schema(
        summary="Обновить тип аудитории",
        description="Обновляет тип аудитории",
        tags=["Типы аудиторий"]
    ),
    partial_update=extend_schema(
        summary="Частично обновить тип аудитории",
        description="Частично обновляет тип аудитории",
        tags=["Типы аудиторий"]
    ),
    destroy=extend_schema(
        summary="Удалить тип аудитории",
        description="Удаляет тип аудитории из системы",
        tags=["Типы аудиторий"]
    ),
)
class AudiencesTypesViewSet(viewsets.ModelViewSet):
    """ViewSet для управления типами аудиторий"""
    
    queryset = AudiencesTypes.objects.all()
    serializer_class = AudiencesTypesSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ['title']
    ordering = ['title']

