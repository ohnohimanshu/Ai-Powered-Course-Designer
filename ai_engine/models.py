# ai_engine/models.py
"""
Models for AI/LLM operations and logging.

This app will house AI-related services in later phases.
For now, defines logging models for debugging and audit trail.
"""
from django.db import models
from django.utils import timezone


class LLMPromptLog(models.Model):
    """
    Audit trail for all LLM interactions.
    
    Logs every prompt sent to the LLM and its response for:
    - Debugging prompt engineering
    - Monitoring LLM behavior
    - Analyzing token usage
    - Compliance and auditing
    """
    PROMPT_TYPE_CHOICES = [
        ('course_generation', 'Course Generation'),
        ('lesson_content', 'Lesson Content'),
        ('evaluation_questions', 'Evaluation Questions'),
        ('feedback', 'Feedback Generation'),
        ('other', 'Other'),
    ]
    
    prompt_type = models.CharField(
        max_length=50,
        choices=PROMPT_TYPE_CHOICES,
        db_index=True,
        help_text="Category of prompt"
    )
    input_prompt = models.TextField(
        help_text="The full prompt sent to the LLM"
    )
    context = models.TextField(
        blank=True,
        help_text="Retrieved context (RAG) used in the prompt"
    )
    response = models.TextField(
        help_text="LLM's response"
    )
    model_name = models.CharField(
        max_length=100,
        help_text="Name of the LLM model used (e.g., 'phi', 'mistral')"
    )
    tokens_used = models.IntegerField(
        null=True,
        blank=True,
        help_text="Approximate token count (if available)"
    )
    execution_time_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Time taken for LLM response (milliseconds)"
    )
    success = models.BooleanField(
        default=True,
        help_text="Whether the LLM call succeeded"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error details if the call failed"
    )
    metadata = models.JSONField(
        default=dict,
        help_text="Additional metadata (temperature, max_tokens, etc.)"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['prompt_type', 'created_at']),
            models.Index(fields=['model_name', 'created_at']),
            models.Index(fields=['success']),
        ]
        verbose_name = "LLM Prompt Log"
        verbose_name_plural = "LLM Prompt Logs"

    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} {self.get_prompt_type_display()} - {self.model_name} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
