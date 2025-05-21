from django.contrib import admin
from .models import Teachers, Students, SubjectsTypes, Schedule, Subjects


@admin.register(Teachers)
class TeachersAdmin(admin.ModelAdmin):
    list_display = ['user',]
    list_filter = ['position',]
    search_fields = ['user', 'position',]


@admin.register(Students)
class StudentsAdmin(admin.ModelAdmin):
    list_display = ['user',]
    list_filter = ['groups',]
    search_fields = ['user', 'groups',]


@admin.register(SubjectsTypes)
class SubjectsTypesAdmin(admin.ModelAdmin):
    list_display = ['title',]
    search_fields = ['title',]


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['week_day', 'week_type', 'time',]
    list_filter = ['time', 'week_day',]


@admin.register(Subjects)
class SubjectsAdmin(admin.ModelAdmin):
    list_display = ['title',]
    list_filter = ['schedule', 'teachers', 'groups']
    search_fields = ['title', 'teachers', 'groups']
