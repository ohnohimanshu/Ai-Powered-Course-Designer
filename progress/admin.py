# progress/admin.py
"""Admin configuration for progress tracking models."""
from django.contrib import admin
from .models import LessonProgress, CourseProgress


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    """Admin interface for lesson progress tracking."""
    list_display = [
        'user', 'lesson', 'score', 'completed', 'attempts', 
        'time_spent_minutes', 'last_accessed'
    ]
    list_filter = ['completed', 'lesson__module__course', 'last_accessed']
    search_fields = ['user__username', 'lesson__title', 'lesson__module__title']
    readonly_fields = ['created_at', 'updated_at', 'last_accessed']
    
    fieldsets = [
        ('Progress Information', {
            'fields': ['user', 'lesson', 'completed', 'score', 'attempts']
        }),
        ('Time Tracking', {
            'fields': ['started_at', 'completed_at', 'time_spent_minutes', 'review_count']
        }),
        ('Metadata', {
            'fields': ['metadata', 'last_accessed', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]


@admin.register(CourseProgress)
class CourseProgressAdmin(admin.ModelAdmin):
    """Admin interface for course progress tracking."""
    list_display = [
        'user', 'course', 'current_lesson', 'overall_score', 
        'started_at', 'completed_at'
    ]
    list_filter = ['completed_at', 'course', 'started_at']
    search_fields = ['user__username', 'course__topic']
    readonly_fields = ['started_at', 'last_accessed', 'updated_at']
    
    fieldsets = [
        ('Course Progress', {
            'fields': ['user', 'course', 'current_lesson', 'overall_score']
        }),
        ('Timing', {
            'fields': ['started_at', 'completed_at', 'last_accessed']
        }),
        ('Metadata', {
            'fields': ['metadata', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
