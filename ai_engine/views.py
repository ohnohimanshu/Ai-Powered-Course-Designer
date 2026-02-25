# ai_engine/views.py
"""
API views for the ai_engine app.

Provides read-only access to LLM prompt logs for auditing.
"""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import LLMPromptLog
from .serializers import LLMPromptLogSerializer


class LLMPromptLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for LLMPromptLog.
    
    Used for auditing and debugging LLM interactions.
    Admin users can view all logs.
    """
    serializer_class = LLMPromptLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return prompt logs with optional filtering."""
        queryset = LLMPromptLog.objects.all()
        
        # Filter by operation type
        operation = self.request.query_params.get('operation_type')
        if operation:
            queryset = queryset.filter(operation_type=operation)
        
        # Filter by model name
        model = self.request.query_params.get('model')
        if model:
            queryset = queryset.filter(model_name__icontains=model)
        
        return queryset.order_by('-created_at')
