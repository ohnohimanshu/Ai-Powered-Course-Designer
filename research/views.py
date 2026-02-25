# research/views.py
"""
API views for the research app.

Provides ViewSets for Resource and ResourceChunk models.
Resources are read-only for regular users.
"""
import logging
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Resource, ResourceChunk, EmbeddingIndex
from .serializers import (
    ResourceSerializer, ResourceDetailSerializer,
    ResourceChunkSerializer, EmbeddingIndexSerializer
)

logger = logging.getLogger(__name__)


class ResourceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for Resources.
    
    Provides list and retrieve operations for learning resources.
    Filtering and search enabled.
    Also provides a research_topic action to trigger topic research.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'transcript_text']
    ordering_fields = ['created_at', 'title', 'resource_type']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return all resources with optional filtering."""
        queryset = Resource.objects.all()
        
        # Filter by resource type
        resource_type = self.request.query_params.get('resource_type')
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return ResourceDetailSerializer
        return ResourceSerializer

    @action(detail=False, methods=['post'])
    def research_topic(self, request):
        """
        Trigger research for a topic.

        POST /api/resources/research_topic/
        Body: {"topic": "Python Generators"}

        Runs YouTube + documentation research pipeline:
        searches, fetches content, chunks, and indexes into vector store.
        """
        topic = request.data.get('topic', '').strip()
        if not topic:
            return Response(
                {'error': 'topic is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from .researcher import ResearchOrchestrator
            resources = ResearchOrchestrator.research_topic(topic)

            return Response({
                'topic': topic,
                'resources_found': len(resources),
                'resources': [
                    {
                        'type': r.get('type'),
                        'title': r.get('title'),
                        'url': r.get('url'),
                        'text_length': len(r.get('text', '')),
                    }
                    for r in resources
                ]
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Research failed for topic '{topic}': {e}")
            return Response(
                {'error': f'Research failed: {str(e)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class ResourceChunkViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for ResourceChunks.
    
    Useful for inspecting how resources are chunked.
    """
    serializer_class = ResourceChunkSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return chunks, optionally filtered by resource."""
        queryset = ResourceChunk.objects.select_related('resource')
        
        # Filter by resource
        resource_id = self.request.query_params.get('resource')
        if resource_id:
            queryset = queryset.filter(resource_id=resource_id)
        
        return queryset.order_by('resource', 'chunk_index')


class EmbeddingIndexViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for EmbeddingIndexes.
    
    For viewing vector store metadata.
    """
    queryset = EmbeddingIndex.objects.all().order_by('-updated_at')
    serializer_class = EmbeddingIndexSerializer
    permission_classes = [IsAuthenticated]
