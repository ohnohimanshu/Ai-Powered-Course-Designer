# ai_engine/serializers.py
"""
Serializers for the ai_engine app.

Handles serialization of LLMPromptLog for auditing purposes.
"""
from rest_framework import serializers
from .models import LLMPromptLog


class LLMPromptLogSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for LLMPromptLog.
    
    Used for auditing and debugging LLM interactions.
    """
    
    class Meta:
        model = LLMPromptLog
        fields = [
            'id', 'operation_type', 'prompt_text', 'response_text',
            'model_name', 'tokens_used', 'cost_usd', 'latency_seconds',
            'metadata', 'created_at'
        ]
        read_only_fields = '__all__'
