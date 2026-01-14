from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import StudyGroupsViewSet

app_name = 'groups'

router = DefaultRouter()
router.register(r'study-groups', StudyGroupsViewSet, basename='study-group')

urlpatterns = [
    path('', include(router.urls)),
]
