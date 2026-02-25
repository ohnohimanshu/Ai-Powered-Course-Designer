# courses/views.py
"""
API views for the courses app.

Provides ViewSets for Course, Module, and Lesson models with
full CRUD operations and custom actions.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404
from django.http import StreamingHttpResponse

from .models import Course, Module, Lesson
from .generators import CourseGenerator
from .serializers import (
    CourseSerializer, CourseListSerializer, CourseDetailSerializer,
    ModuleSerializer, LessonSerializer
)
from .permissions import IsOwnerOrReadOnly, IsCourseOwner
from progress.models import CourseProgress, LessonProgress


class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Course management.
    """
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        """Return courses for the authenticated user."""
        user = self.request.user
        queryset = Course.objects.filter(user=user).select_related('user')
        
        # Optimize for list view
        if self.action == 'list':
            queryset = queryset.annotate(
                module_count=Count('modules', distinct=True),
                lesson_count=Count('modules__lessons', distinct=True)
            )
        # Optimize for detail view
        elif self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                Prefetch('modules', queryset=Module.objects.select_related().prefetch_related('lessons'))
            )
        
        # Apply filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        level_filter = self.request.query_params.get('level')
        if level_filter:
            queryset = queryset.filter(level=level_filter)
        
        # Ordering
        ordering = self.request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return CourseListSerializer
        elif self.action == 'retrieve':
            return CourseDetailSerializer
        return CourseSerializer
    
    def perform_create(self, serializer):
        """Set the user when creating a course."""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Generates a new course structure using AI.
        Body: {
            "topic": "Python", 
            "level": "beginner", 
            "goal": "Learn basics"
        }
        """
        topic = request.data.get('topic')
        level = request.data.get('level', 'beginner')
        goal = request.data.get('goal', f"Learn about {topic}")
        
        if not topic:
            return Response(
                {'error': 'Topic is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            course = CourseGenerator.generate_course_structure(
                user=request.user,
                topic=topic,
                level=level,
                goal=goal
            )
            serializer = CourseDetailSerializer(course, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            # logger.error(e) 
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """
        Get user's progress for this course.
        """
        course = self.get_object()
        
        try:
            course_progress = CourseProgress.objects.get(
                user=request.user,
                course=course
            )
            from progress.serializers import CourseProgressSerializer
            serializer = CourseProgressSerializer(course_progress, context={'request': request})
            return Response(serializer.data)
        except CourseProgress.DoesNotExist:
            return Response(
                {'detail': 'Course progress not found. Start the course first.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def next_lesson(self, request, pk=None):
        """
        Get the next lesson for the user to take.
        """
        course = self.get_object()
        
        try:
            course_progress = CourseProgress.objects.select_related('current_lesson').get(
                user=request.user,
                course=course
            )
            
            if course_progress.current_lesson:
                serializer = LessonSerializer(
                    course_progress.current_lesson,
                    context={'request': request}
                )
                return Response(serializer.data)
            else:
                return Response(
                    {'detail': 'Course completed! No more lessons.'},
                    status=status.HTTP_200_OK
                )
        except CourseProgress.DoesNotExist:
            # Not started, return first lesson
            first_module = course.modules.first()
            if first_module:
                first_lesson = first_module.lessons.first()
                if first_lesson:
                    serializer = LessonSerializer(first_lesson, context={'request': request})
                    return Response(serializer.data)
            
            return Response(
                {'detail': 'No lessons available in this course.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """
        Initialize course progress for the user.
        """
        course = self.get_object()
        
        # Check if already started
        course_progress, created = CourseProgress.objects.get_or_create(
            user=request.user,
            course=course
        )
        
        if created:
            # Set the first lesson as current
            first_module = course.modules.first()
            if first_module:
                first_lesson = first_module.lessons.first()
                if first_lesson:
                    course_progress.current_lesson = first_lesson
                    course_progress.save()
        
        from progress.serializers import CourseProgressSerializer
        serializer = CourseProgressSerializer(course_progress, context={'request': request})
        
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class ModuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Module management.
    """
    serializer_class = ModuleSerializer
    permission_classes = [IsAuthenticated, IsCourseOwner]
    
    def get_queryset(self):
        """Return modules for courses owned by the user."""
        user = self.request.user
        queryset = Module.objects.filter(
            course__user=user
        ).select_related('course').prefetch_related('lessons')
        
        # Filter by course if provided
        course_id = self.request.query_params.get('course')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        return queryset.order_by('order')
    
    def perform_create(self, serializer):
        """Validate course ownership when creating a module."""
        course = serializer.validated_data.get('course')
        if course.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only add modules to your own courses.")
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def reorder(self, request, pk=None):
        """
        Change the order of this module.
        """
        module = self.get_object()
        new_order = request.data.get('new_order')
        
        if not new_order or new_order < 1:
            return Response(
                {'detail': 'new_order must be a positive integer.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        module.order = new_order
        module.save()
        
        serializer = self.get_serializer(module)
        return Response(serializer.data)


class LessonViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Lesson management.
    """
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsCourseOwner]
    
    def get_queryset(self):
        """Return lessons for courses owned by the user."""
        user = self.request.user
        queryset = Lesson.objects.filter(
            module__course__user=user
        ).select_related('module', 'module__course').prefetch_related('resources')
        
        # Filter by module if provided
        module_id = self.request.query_params.get('module')
        if module_id:
            queryset = queryset.filter(module_id=module_id)
        
        return queryset.order_by('order')
    
    def perform_create(self, serializer):
        """Validate course ownership when creating a lesson."""
        module = serializer.validated_data.get('module')
        if module.course.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only add lessons to your own courses.")
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def generate_content(self, request, pk=None):
        """
        Generates content for this lesson using AI (Streaming).
        Returns a text/event-stream response.
        """
        lesson = self.get_object()
        
        try:
            # Use StreamingHttpResponse with the sync generator
            stream = CourseGenerator.generate_lesson_content_stream(lesson)
            response = StreamingHttpResponse(stream, content_type='text/event-stream')
            response['Cache-Control'] = 'no-cache'
            return response
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
    
    @action(detail=True, methods=['get'])
    def next(self, request, pk=None):
        """
        Get the next lesson in sequence.
        """
        lesson = self.get_object()
        next_lesson = lesson.get_next_lesson()
        
        if next_lesson:
            serializer = self.get_serializer(next_lesson)
            return Response(serializer.data)
        
        return Response(
            {'detail': 'This is the last lesson in the course.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    @action(detail=True, methods=['get'])
    def previous(self, request, pk=None):
        """
        Get the previous lesson in sequence.
        """
        lesson = self.get_object()
        prev_lesson = lesson.get_previous_lesson()
        
        if prev_lesson:
            serializer = self.get_serializer(prev_lesson)
            return Response(serializer.data)
        
        return Response(
            {'detail': 'This is the first lesson in the course.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Mark this lesson as completed for the user.
        """
        lesson = self.get_object()
        score = request.data.get('score')
        
        # Get or create lesson progress
        lesson_progress, created = LessonProgress.objects.get_or_create(
            user=request.user,
            lesson=lesson
        )
        
        # Mark as started if not already
        if not lesson_progress.started_at:
            lesson_progress.mark_started()
        
        # Mark as completed
        lesson_progress.mark_completed(score=score)
        
        # Update course progress
        course = lesson.module.course
        course_progress, _ = CourseProgress.objects.get_or_create(
            user=request.user,
            course=course
        )
        course_progress.update_overall_score()
        course_progress.advance_to_next_lesson()
        
        from progress.serializers import LessonProgressSerializer
        serializer = LessonProgressSerializer(lesson_progress, context={'request': request})
        
        return Response(serializer.data, status=status.HTTP_200_OK)
