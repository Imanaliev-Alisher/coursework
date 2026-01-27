from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    TimeSlotViewSet,
    DayViewSet,
    SubjectsTypesViewSet,
    SubjectScheduleViewSet,
    SubjectsViewSet,
    ScheduleGeneratorViewSet,
)

app_name = 'studies'

router = DefaultRouter()
router.register(r'time-slots', TimeSlotViewSet, basename='timeslot')
router.register(r'days', DayViewSet, basename='day')
router.register(r'subject-types', SubjectsTypesViewSet, basename='subject-type')
router.register(r'subject-schedules', SubjectScheduleViewSet, basename='subject-schedule')
router.register(r'subjects', SubjectsViewSet, basename='subject')
router.register(r'schedule-generator', ScheduleGeneratorViewSet, basename='schedule-generator')

urlpatterns = [
    path('', include(router.urls)),
]
