# research/models.py
"""
Models for storing researched learning materials and embeddings.

This app handles:
- Raw learning resources (YouTube videos, documentation, articles)
- Text chunking for embeddings
- Vector store metadata
"""
from django.db import models
from django.utils import timezone


class Resource(models.Model):
    """
    Stores researched learning materials from various sources.
    
    These are raw materials that can be linked to lessons and used
    for RAG-based content generation.
    """
    RESOURCE_TYPE_CHOICES = [
        ('youtube', 'YouTube Video'),
        ('documentation', 'Documentation'),
        ('article', 'Article'),
        ('book', 'Book'),
        ('other', 'Other'),
    ]
    
    resource_type = models.CharField(
        max_length=20,
        choices=RESOURCE_TYPE_CHOICES,
        db_index=True,
        help_text="Type of learning resource"
    )
    url = models.URLField(
        max_length=500,
        unique=True,
        help_text="Original URL of the resource"
    )
    title = models.CharField(
        max_length=500,
        help_text="Title of the resource"
    )
    description = models.TextField(
        blank=True,
        help_text="Brief description or summary"
    )
    transcript_text = models.TextField(
        blank=True,
        help_text="Full transcript or extracted text content"
    )
    metadata = models.JSONField(
        default=dict,
        help_text="Additional metadata (author, duration, views, etc.)"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['resource_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_resource_type_display()}: {self.title}"
    
    def get_chunk_count(self):
        """Returns the number of text chunks for this resource."""
        return self.chunks.count()


class ResourceChunk(models.Model):
    """
    Stores chunked text from resources for embedding generation.
    
    Text is chunked into smaller pieces (300-500 tokens) to:
    - Fit within embedding model limits
    - Enable more precise semantic search
    - Preserve context boundaries
    """
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name='chunks',
        help_text="Parent resource"
    )
    chunk_text = models.TextField(
        help_text="Text content of this chunk"
    )
    chunk_index = models.IntegerField(
        help_text="Sequential index within the resource (0-based)"
    )
    token_count = models.IntegerField(
        default=0,
        help_text="Approximate token count"
    )
    metadata = models.JSONField(
        default=dict,
        help_text="Chunk-specific metadata (timestamp, section, etc.)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['resource', 'chunk_index']
        unique_together = [['resource', 'chunk_index']]
        indexes = [
            models.Index(fields=['resource', 'chunk_index']),
        ]
    
    def __str__(self):
        return f"{self.resource.title} - Chunk {self.chunk_index}"


class EmbeddingIndex(models.Model):
    """
    Tracks FAISS vector store indexes and their metadata.
    
    Each index represents a collection of embeddings for semantic search.
    Multiple indexes can exist for different domains or model versions.
    """
    index_name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique identifier for this index"
    )
    model_name = models.CharField(
        max_length=200,
        help_text="Name of the embedding model used (e.g., 'all-MiniLM-L6-v2')"
    )
    dimension = models.IntegerField(
        help_text="Embedding vector dimension"
    )
    total_vectors = models.IntegerField(
        default=0,
        help_text="Total number of vectors in the index"
    )
    file_path = models.CharField(
        max_length=500,
        help_text="File system path to the persisted FAISS index"
    )
    metadata = models.JSONField(
        default=dict,
        help_text="Additional index metadata (params, stats, etc.)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Embedding Index"
        verbose_name_plural = "Embedding Indexes"
    
    def __str__(self):
        return f"{self.index_name} ({self.total_vectors} vectors)"
