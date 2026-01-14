from django.contrib import admin
from .models import TimeSlot, Day, SubjectsTypes, Schedule, Subjects, ScheduleOverride


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['number', 'start_time', 'end_time']
    list_filter = ['number',]
    ordering = ['number',]


@admin.register(Day)
class DayAdmin(admin.ModelAdmin):
    list_display = ['title',]
    search_fields = ['title',]


@admin.register(SubjectsTypes)
class SubjectsTypesAdmin(admin.ModelAdmin):
    list_display = ['title',]
    search_fields = ['title',]


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['week_day', 'time_slot', 'week_type']
    list_filter = ['week_day', 'time_slot', 'week_type']


@admin.register(Subjects)
class SubjectsAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject_type', 'audience']
    list_filter = ['subject_type', 'groups']
    search_fields = ['title',]
    filter_horizontal = ['schedule', 'teachers', 'groups']


@admin.register(ScheduleOverride)
class ScheduleOverrideAdmin(admin.ModelAdmin):
    list_display = ['subject', 'date', 'time_slot', 'audience', 'is_cancelled']
    list_filter = ['is_cancelled', 'date']
    search_fields = ['subject__title', 'notes']
    ordering = ['-date', 'time_slot__number']

