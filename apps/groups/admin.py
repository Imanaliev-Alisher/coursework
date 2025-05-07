from django.contrib import admin
from .models import StudyGroups


@admin.register(StudyGroups)
class StudyGroupsAdmin(admin.ModelAdmin):
    list_display = ['title',]
    list_filter = ['is_active',]
    search_fields = ['title', 'description',]
