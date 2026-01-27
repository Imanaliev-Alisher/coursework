from django.contrib import admin
from .models import TimeSlot, Day, SubjectsTypes, SubjectSchedule, Subjects


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


@admin.register(SubjectSchedule)
class SubjectScheduleAdmin(admin.ModelAdmin):
    list_display = ['subject', 'week_day', 'time_slot', 'week_type', 'get_teachers', 'get_groups']
    list_filter = ['week_day', 'time_slot', 'week_type', 'subject__subject_type']
    search_fields = ['subject__title']
    raw_id_fields = ['subject']
    
    def get_teachers(self, obj):
        return ", ".join([t.get_full_name() for t in obj.teachers.all()])
    get_teachers.short_description = 'Преподаватели'
    
    def get_groups(self, obj):
        return ", ".join([g.title for g in obj.groups.all()])
    get_groups.short_description = 'Группы'


class SubjectScheduleInline(admin.TabularInline):
    model = SubjectSchedule
    extra = 1
    fields = ['week_day', 'time_slot', 'week_type']
    # teachers и groups редактируются в отдельной админке SubjectSchedule


@admin.register(Subjects)
class SubjectsAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject_type', 'audience']
    list_filter = ['subject_type']
    search_fields = ['title',]
    inlines = [SubjectScheduleInline]
