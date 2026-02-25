# progress/serializers.py
"""
Serializers for the progress app.

Handles serialization of LessonProgress and CourseProgress models.
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import LessonProgress, CourseProgress
from courses.models import Lesson, Course


class LessonProgressSerializer(serializers.ModelSerializer):
    """
    Serializer for LessonProgress model.
    
    Includes nested lesson info and validation for scores.
    """
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    lesson_id = serializers.IntegerField(source='lesson.id', read_only=True)
    module_title = serializers.CharField(source='lesson.module.title', read_only=True)
    course_topic = serializers.CharField(source='lesson.module.course.topic', read_only=True)
    
    class Meta:
        model = LessonProgress
        fields = [
            'id', 'user', 'lesson', 'lesson_id', 'lesson_title',
            'module_title', 'course_topic', 'score', 'completed',
            'attempts', 'started_at', 'completed_at', 'last_accessed',
            'time_spent_minutes', 'review_count', 'metadata',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'user', 'started_at', 'completed_at', 'last_accessed',
            'created_at', 'updated_at'
        ]
    
    def validate_score(self, value):
        """Ensure score is between 0 and 100."""
        if value < 0 or value > 100:
            raise serializers.ValidationError("Score must be between 0 and 100.")
        return value
    
    def validate_time_spent_minutes(self, value):
        """Ensure time spent is non-negative."""
        if value < 0:
            raise serializers.ValidationError("Time spent cannot be negative.")
        return value


class CourseProgressSerializer(serializers.ModelSerializer):
    """
    Serializer for CourseProgress model.
    
    Includes nested course info and calculated completion percentage.
    """
    course_topic = serializers.CharField(source='course.topic', read_only=True)
    course_id = serializers.IntegerField(source='course.id', read_only=True)
    current_lesson_title = serializers.CharField(
        source='current_lesson.title',
        read_only=True,
        allow_null=True
    )
    current_lesson_id = serializers.IntegerField(
        source='current_lesson.id',
        read_only=True,
        allow_null=True
    )
    completion_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseProgress
        fields = [
            'id', 'user', 'course', 'course_id', 'course_topic',
            'current_lesson', 'current_lesson_id', 'current_lesson_title',
            'started_at', 'completed_at', 'overall_score',
            'completion_percentage', 'metadata', 'last_accessed',
            'updated_at'
        ]
        read_only_fields = [
            'user', 'started_at', 'completed_at', 'last_accessed', 'updated_at'
        ]
    
    def get_completion_percentage(self, obj):
        """Calculate percentage of lessons completed."""
        return obj.get_completion_percentage()


class ProgressUpdateSerializer(serializers.Serializer):
    """
    Write-only serializer for updating progress.
    
    Used for atomic progress updates (time, metadata, etc.).
    """
    time_spent_minutes = serializers.IntegerField(
        required=False,
        min_value=0,
        help_text="Minutes to add to time spent"
    )
    metadata = serializers.JSONField(
        required=False,
        help_text="Additional metadata to merge"
    )
    score = serializers.FloatField(
        required=False,
        min_value=0,
        max_value=100,
        help_text="Update the score"
    )
