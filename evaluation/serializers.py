# evaluation/serializers.py
"""
Serializers for the evaluation app.

Handles serialization of EvaluationResult and ConceptMastery models.
"""
from rest_framework import serializers
from .models import EvaluationResult, ConceptMastery


class EvaluationResultSerializer(serializers.ModelSerializer):
    """
    Serializer for EvaluationResult model (Full result with feedback).
    """
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    passed = serializers.SerializerMethodField()
    
    class Meta:
        model = EvaluationResult
        fields = [
            'id', 'user', 'user_username', 'lesson', 'lesson_title',
            'questions', 'answers', 'score', 'passed',
            'feedback', 'concept_mastery', 'created_at'
        ]
        read_only_fields = ['user', 'created_at', 'score', 'feedback', 'concept_mastery', 'questions']
    
    def get_passed(self, obj):
        return obj.is_passing()

class QuizSerializer(serializers.ModelSerializer):
    """
    Serializer for TAKING the quiz (hides correct answers).
    """
    questions = serializers.SerializerMethodField()
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    
    class Meta:
        model = EvaluationResult
        fields = ['id', 'lesson', 'lesson_title', 'questions', 'created_at']
        
    def get_questions(self, obj):
        # Return questions without correct_answer and explanation
        sanitized = []
        for q in obj.questions:
            sanitized.append({
                "text": q.get('text'),
                "type": q.get('type'),
                "options": q.get('options')
            })
        return sanitized


class ConceptMasterySerializer(serializers.ModelSerializer):
    """
    Serializer for ConceptMastery model.
    
    Tracks mastery levels (0-1.0) for individual concepts.
    """
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = ConceptMastery
        fields = [
            'id', 'user', 'user_username', 'lesson', 'lesson_title',
            'concept_name', 'mastery_level', 'practice_count',
            'last_practiced', 'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'last_practiced', 'created_at', 'updated_at']
    
    def validate_mastery_level(self, value):
        """Ensure mastery level is between 0 and 1."""
        if value < 0.0 or value > 1.0:
            raise serializers.ValidationError("Mastery level must be between 0.0 and 1.0.")
        return value
    
    def validate_concept_name(self, value):
        """Ensure concept name is not empty."""
        if not value.strip():
            raise serializers.ValidationError("Concept name cannot be empty.")
        return value
