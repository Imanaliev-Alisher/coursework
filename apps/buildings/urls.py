from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import BuildingsViewSet, AudiencesViewSet, AudiencesTypesViewSet

app_name = 'buildings'

router = DefaultRouter()
router.register(r'buildings', BuildingsViewSet, basename='building')
router.register(r'audiences', AudiencesViewSet, basename='audience')
router.register(r'audience-types', AudiencesTypesViewSet, basename='audience-type')

urlpatterns = [
    path('', include(router.urls)),
]
