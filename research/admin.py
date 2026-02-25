# research/admin.py
"""Admin configuration for research app models."""
from django.contrib import admin
from .models import Resource, ResourceChunk, EmbeddingIndex


class ResourceChunkInline(admin.TabularInline):
    """Inline editor for resource chunks."""
    model = ResourceChunk
    extra = 0
    fields = ['chunk_index', 'token_count', 'chunk_text']
    readonly_fields = ['chunk_index']


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    """Admin interface for learning resources."""
    list_display = ['title', 'resource_type', 'url', 'get_chunk_count', 'created_at']
    list_filter = ['resource_type', 'created_at']
    search_fields = ['title', 'description', 'url']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ResourceChunkInline]
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['resource_type', 'title', 'url', 'description']
        }),
        ('Content', {
            'fields': ['transcript_text', 'metadata']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]


@admin.register(ResourceChunk)
class ResourceChunkAdmin(admin.ModelAdmin):
    """Admin interface for resource chunks."""
    list_display = ['resource', 'chunk_index', 'token_count', 'created_at']
    list_filter = ['resource__resource_type', 'created_at']
    search_fields = ['resource__title', 'chunk_text']
    readonly_fields = ['created_at']


@admin.register(EmbeddingIndex)
class EmbeddingIndexAdmin(admin.ModelAdmin):
    """Admin interface for embedding indexes."""
    list_display = ['index_name', 'model_name', 'dimension', 'total_vectors', 'updated_at']
    search_fields = ['index_name', 'model_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Index Information', {
            'fields': ['index_name', 'model_name', 'dimension', 'total_vectors']
        }),
        ('Storage', {
            'fields': ['file_path', 'metadata']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
