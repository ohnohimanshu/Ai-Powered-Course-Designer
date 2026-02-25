# ai_engine/admin.py
"""Admin configuration for AI engine models."""
from django.contrib import admin
from .models import LLMPromptLog


@admin.register(LLMPromptLog)
class LLMPromptLogAdmin(admin.ModelAdmin):
    """Admin interface for LLM prompt logging."""
    list_display = [
        'prompt_type', 'model_name', 'success', 'tokens_used', 
        'execution_time_ms', 'created_at'
    ]
    list_filter = ['prompt_type', 'model_name', 'success', 'created_at']
    search_fields = ['input_prompt', 'response', 'error_message']
    readonly_fields = ['created_at']
    
    fieldsets = [
        ('Prompt Information', {
            'fields': ['prompt_type', 'model_name', 'success']
        }),
        ('Prompt & Response', {
            'fields': ['input_prompt', 'context', 'response']
        }),
        ('Performance Metrics', {
            'fields': ['tokens_used', 'execution_time_ms', 'error_message']
        }),
        ('Metadata', {
            'fields': ['metadata', 'created_at'],
            'classes': ['collapse']
        }),
    ]
    
    def has_add_permission(self, request):
        """Prevent manual creation of logs (auto-generated only)."""
        return False
