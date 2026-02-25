# courses/serializers.py
"""
Serializers for the courses app.

Handles serialization/deserialization of Course, Module, and Lesson models
for the REST API.
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Course, Module, Lesson
from research.models import Resource


class ResourceMinimalSerializer(serializers.ModelSerializer):
    """Minimal resource info for nested display."""
    
    class Meta:
        model = Resource
        fields = ['id', 'resource_type', 'title', 'url']


class LessonSerializer(serializers.ModelSerializer):
    """
    Serializer for Lesson model.
    
    Includes nested resources (read-only) and navigation methods.
    """
    resources = ResourceMinimalSerializer(many=True, read_only=True)
    resource_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Resource.objects.all(),
        write_only=True,
        required=False,
        source='resources'
    )
    module_title = serializers.CharField(source='module.title', read_only=True)
    course_id = serializers.IntegerField(source='module.course.id', read_only=True)
    course_topic = serializers.CharField(source='module.course.topic', read_only=True)
    next_lesson = serializers.SerializerMethodField()
    previous_lesson = serializers.SerializerMethodField()
    is_completed = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'module', 'module_title', 'course_id', 'course_topic',
            'title', 'content', 'content_type',
            'order', 'estimated_duration_minutes', 'objectives',
            'resources', 'resource_ids', 'prerequisites',
            'next_lesson', 'previous_lesson', 'is_completed',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_next_lesson(self, obj):
        """Get the next lesson in sequence."""
        next_lesson = obj.get_next_lesson()
        if next_lesson:
            return {'id': next_lesson.id, 'title': next_lesson.title}
        return None
    
    def get_previous_lesson(self, obj):
        """Get the previous lesson in sequence."""
        prev_lesson = obj.get_previous_lesson()
        if prev_lesson:
            return {'id': prev_lesson.id, 'title': prev_lesson.title}
        return None
    
    def get_is_completed(self, obj):
        """Check if current user has completed this lesson."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.is_completed(request.user)
        return False


class LessonMinimalSerializer(serializers.ModelSerializer):
    """Minimal lesson info for nested display in modules."""
    
    is_completed = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'order', 'content_type', 'estimated_duration_minutes', 'is_completed']
    
    def get_is_completed(self, obj):
        """Check if current user has completed this lesson."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.is_completed(request.user)
        return False


class ModuleSerializer(serializers.ModelSerializer):
    """
    Serializer for Module model.
    
    Includes nested lessons (read-only) and completion status.
    """
    lessons = LessonMinimalSerializer(many=True, read_only=True)
    lesson_count = serializers.SerializerMethodField()
    is_completed = serializers.SerializerMethodField()
    
    class Meta:
        model = Module
        fields = [
            'id', 'course', 'title', 'description', 'order',
            'objectives', 'lessons', 'lesson_count', 'is_completed',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_lesson_count(self, obj):
        """Returns total number of lessons in this module."""
        return obj.get_lesson_count()
    
    def get_is_completed(self, obj):
        """Check if current user has completed all lessons in this module."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.is_completed(request.user)
        return False
    
    def validate_order(self, value):
        """Ensure order is positive."""
        if value < 1:
            raise serializers.ValidationError("Order must be a positive integer.")
        return value


class ModuleMinimalSerializer(serializers.ModelSerializer):
    """Minimal module info for nested display in courses."""
    
    lesson_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Module
        fields = ['id', 'title', 'order', 'lesson_count']


class CourseListSerializer(serializers.ModelSerializer):
    """
    Optimized serializer for course listings.
    
    Minimal fields for performance in list views.
    """
    module_count = serializers.IntegerField(read_only=True)
    lesson_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id', 'user', 'topic', 'level', 'status',
            'module_count', 'lesson_count', 'created_at'
        ]


class CourseSerializer(serializers.ModelSerializer):
    """
    Main serializer for Course model.
    
    Includes nested modules and calculated fields.
    """
    modules = ModuleMinimalSerializer(many=True, read_only=True)
    module_count = serializers.SerializerMethodField()
    lesson_count = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id', 'user', 'user_username', 'topic', 'level', 'goal',
            'status', 'estimated_duration_hours', 'description',
            'modules', 'module_count', 'lesson_count', 'progress_percentage',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def get_module_count(self, obj):
        """Returns total number of modules."""
        return obj.get_module_count()
    
    def get_lesson_count(self, obj):
        """Returns total number of lessons."""
        return obj.get_lesson_count()
    
    def get_progress_percentage(self, obj):
        """Calculate completion percentage for current user."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_progress_percentage(request.user)
        return 0.0
    
    def validate_topic(self, value):
        """Ensure topic is not empty."""
        if not value.strip():
            raise serializers.ValidationError("Topic cannot be empty.")
        return value
    
    def validate_estimated_duration_hours(self, value):
        """Ensure duration is positive."""
        if value <= 0:
            raise serializers.ValidationError("Duration must be a positive number.")
        return value
    
    def create(self, validated_data):
        """Set the user from the request context."""
        request = self.context.get('request')
        if request and request.user:
            validated_data['user'] = request.user
        return super().create(validated_data)


class CourseDetailSerializer(CourseSerializer):
    """
    Detailed serializer with full nested structure.
    
    Used for retrieve operations with all modules and lessons.
    """
    modules = ModuleSerializer(many=True, read_only=True)
    
    class Meta(CourseSerializer.Meta):
        pass
