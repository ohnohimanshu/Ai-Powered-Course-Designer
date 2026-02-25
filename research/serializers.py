# research/serializers.py
"""
Serializers for the research app.

Handles serialization of Resource, ResourceChunk, and EmbeddingIndex models.
"""
from rest_framework import serializers
from .models import Resource, ResourceChunk, EmbeddingIndex


class ResourceChunkSerializer(serializers.ModelSerializer):
    """Serializer for ResourceChunk model."""
    
    class Meta:
        model = ResourceChunk
        fields = [
            'id', 'resource', 'chunk_text', 'chunk_index',
            'token_count', 'metadata', 'created_at'
        ]
        read_only_fields = ['created_at']


class ResourceSerializer(serializers.ModelSerializer):
    """
    Serializer for Resource model.
    
    Includes chunk count and validation for URLs and resource types.
    """
    chunk_count = serializers.SerializerMethodField()
    resource_type_display = serializers.CharField(
        source='get_resource_type_display',
        read_only=True
    )
    
    class Meta:
        model = Resource
        fields = [
            'id', 'resource_type', 'resource_type_display', 'url',
            'title', 'description', 'transcript_text', 'metadata',
            'chunk_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_chunk_count(self, obj):
        """Returns the number of text chunks for this resource."""
        return obj.get_chunk_count()
    
    def validate_url(self, value):
        """Validate URL format and length."""
        if len(value) > 500:
            raise serializers.ValidationError("URL is too long (max 500 characters).")
        return value
    
    def validate_title(self, value):
        """Ensure title is not empty."""
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value


class ResourceDetailSerializer(ResourceSerializer):
    """
    Detailed resource serializer with all chunks.
    
    Used for retrieve operations.
    """
    chunks = ResourceChunkSerializer(many=True, read_only=True)
    
    class Meta(ResourceSerializer.Meta):
        fields = ResourceSerializer.Meta.fields + ['chunks']


class EmbeddingIndexSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for EmbeddingIndex.
    
    Index management will be handled in Phase 3.
    """
    
    class Meta:
        model = EmbeddingIndex
        fields = [
            'id', 'index_name', 'model_name', 'dimension',
            'total_vectors', 'file_path', 'metadata',
            'created_at', 'updated_at'
        ]
        read_only_fields = '__all__'
