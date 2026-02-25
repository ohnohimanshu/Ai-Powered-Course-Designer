# evaluation/admin.py
"""Admin configuration for evaluation models."""
from django.contrib import admin
from .models import EvaluationResult, ConceptMastery


@admin.register(EvaluationResult)
class EvaluationResultAdmin(admin.ModelAdmin):
    """Admin interface for evaluation results."""
    list_display = ['user', 'lesson', 'score', 'created_at']
    list_filter = ['created_at', 'lesson__module__course']
    search_fields = ['user__username', 'lesson__title']
    readonly_fields = ['created_at']
    
    fieldsets = [
        ('Evaluation Information', {
            'fields': ['user', 'lesson', 'score', 'created_at']
        }),
        ('Questions & Answers', {
            'fields': ['questions', 'answers', 'feedback']
        }),
        ('Concept Mastery', {
            'fields': ['concept_mastery'],
            'description': 'Mapping of concept names to mastery levels (0.0-1.0)'
        }),
    ]


@admin.register(ConceptMastery)
class ConceptMasteryAdmin(admin.ModelAdmin):
    """Admin interface for concept mastery tracking."""
    list_display = [
        'user', 'lesson', 'concept_name', 'mastery_level', 
        'attempts', 'last_evaluated'
    ]
    list_filter = ['lesson__module__course', 'last_evaluated']
    search_fields = ['user__username', 'concept_name', 'lesson__title']
    readonly_fields = ['created_at', 'last_evaluated']
    
    fieldsets = [
        ('Concept Information', {
            'fields': ['user', 'lesson', 'concept_name']
        }),
        ('Mastery Tracking', {
            'fields': ['mastery_level', 'attempts', 'last_evaluated']
        }),
        ('Metadata', {
            'fields': ['metadata', 'created_at'],
            'classes': ['collapse']
        }),
    ]
