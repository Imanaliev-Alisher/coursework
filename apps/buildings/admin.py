from django.contrib import admin
from .models import Buildings, AudiencesTypes, Audiences


@admin.register(Buildings)
class BuildingsAdmin(admin.ModelAdmin):
    list_display = ['title', 'address',]
    list_filter = ['country', 'region', 'city', 'street', 'house_number',]
    search_fields = ['title', 'address',]
    

@admin.register(AudiencesTypes)
class AudiencesTypesAdmin(admin.ModelAdmin):
    list_display = ['title',]
    search_fields = ['title',]
    

@admin.register(Audiences)
class AudiencesAdmin(admin.ModelAdmin):
    list_display = ['title', 'building',]
    list_filter = ['auditorium_type', 'floor_number',]
    search_fields = ['title', 'building', 'auditorium_number',]
