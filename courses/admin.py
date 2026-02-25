# courses/admin.py
"""Admin configuration for courses app models."""
from django.contrib import admin
from .models import Course, Module, Lesson


class LessonInline(admin.TabularInline):
    """Inline editor for lessons within a module."""
    model = Lesson
    extra = 0
    fields = ['order', 'title', 'content_type', 'estimated_duration_minutes']
    ordering = ['order']


class ModuleInline(admin.StackedInline):
    """Inline editor for modules within a course."""
    model = Module
    extra = 0
    fields = ['order', 'title', 'description', 'objectives', 'estimated_duration_hours']
    ordering = ['order']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Admin interface for courses with nested module creation."""
    list_display = ['topic', 'user', 'level', 'status', 'get_module_count', 'get_lesson_count', 'created_at']
    list_filter = ['status', 'level', 'created_at']
    search_fields = ['topic', 'description', 'goal', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'get_module_count', 'get_lesson_count']
    inlines = [ModuleInline]
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['user', 'topic', 'level', 'goal']
        }),
        ('Course Details', {
            'fields': ['description', 'estimated_duration_hours', 'status']
        }),
        ('Metadata', {
            'fields': ['get_module_count', 'get_lesson_count', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def get_module_count(self, obj):
        """Display module count in admin."""
        return obj.get_module_count()
    get_module_count.short_description = 'Modules'
    
    def get_lesson_count(self, obj):
        """Display lesson count in admin."""
        return obj.get_lesson_count()
    get_lesson_count.short_description = 'Lessons'


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    """Admin interface for modules with nested lesson creation."""
    list_display = ['title', 'course', 'order', 'get_lesson_count', 'estimated_duration_hours']
    list_filter = ['course', 'course__level']
    search_fields = ['title', 'description', 'course__topic']
    readonly_fields = ['created_at', 'updated_at', 'get_lesson_count']
    inlines = [LessonInline]
    
    fieldsets = [
        ('Module Information', {
            'fields': ['course', 'order', 'title', 'description']
        }),
        ('Learning Objectives', {
            'fields': ['objectives', 'estimated_duration_hours']
        }),
        ('Metadata', {
            'fields': ['get_lesson_count', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def get_lesson_count(self, obj):
        """Display lesson count in admin."""
        return obj.get_lesson_count()
    get_lesson_count.short_description = 'Lessons'


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """Admin interface for lessons."""
    list_display = ['title', 'module', 'order', 'content_type', 'estimated_duration_minutes']
    list_filter = ['content_type', 'module__course__level', 'module__course']
    search_fields = ['title', 'description', 'content', 'module__title']
    filter_horizontal = ['resources']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Lesson Information', {
            'fields': ['module', 'order', 'title', 'description', 'content_type']
        }),
        ('Content', {
            'fields': ['content', 'objectives', 'prerequisites']
        }),
        ('Resources', {
            'fields': ['resources', 'estimated_duration_minutes']
        }),
        ('Metadata', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
