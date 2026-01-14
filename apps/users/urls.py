from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, StudentViewSet, TeacherViewSet

app_name = 'users'

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'students', StudentViewSet, basename='student')
router.register(r'teachers', TeacherViewSet, basename='teacher')

urlpatterns = [
    path('', include(router.urls)),
]
