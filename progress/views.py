# progress/views.py
"""
API views for the progress app.

Provides ViewSets for LessonProgress and CourseProgress tracking.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import LessonProgress, CourseProgress
from .serializers import (
    LessonProgressSerializer, CourseProgressSerializer,
    ProgressUpdateSerializer
)


class LessonProgressViewSet(viewsets.ModelViewSet):
    """
    ViewSet for LessonProgress tracking.
    
    Users can view and update their own lesson progress.
    """
    serializer_class = LessonProgressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return lesson progress for the authenticated user."""
        queryset = LessonProgress.objects.filter(
            user=self.request.user
        ).select_related('lesson', 'lesson__module', 'lesson__module__course')
        
        # Filter by course
        course_id = self.request.query_params.get('course')
        if course_id:
            queryset = queryset.filter(lesson__module__course_id=course_id)
        
        # Filter by completion status
        completed = self.request.query_params.get('completed')
        if completed is not None:
            completed_bool = completed.lower() == 'true'
            queryset = queryset.filter(completed=completed_bool)
        
        # Filter by lesson
        lesson_id = self.request.query_params.get('lesson')
        if lesson_id:
            queryset = queryset.filter(lesson_id=lesson_id)
        
        return queryset.order_by('-last_accessed')
    
    def perform_create(self, serializer):
        """Set the user when creating progress."""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """
        Mark the lesson as started.
        
        POST /api/lesson-progress/{id}/start/
        """
        progress = self.get_object()
        progress.mark_started()
        
        serializer = self.get_serializer(progress)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Mark the lesson as completed.
        
        POST /api/lesson-progress/{id}/complete/
        Body: {"score": 85} (optional)
        """
        progress = self.get_object()
        score = request.data.get('score')
        
        # Mark as started if not already
        if not progress.started_at:
            progress.mark_started()
        
        progress.mark_completed(score=score)
        
        serializer = self.get_serializer(progress)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_time(self, request, pk=None):
        """
        Add time spent on this lesson.
        
        POST /api/lesson-progress/{id}/update-time/
        Body: {"minutes": 15}
        """
        progress = self.get_object()
        minutes = request.data.get('minutes', 0)
        
        if minutes < 0:
            return Response(
                {'detail': 'Minutes must be non-negative.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        progress.update_time_spent(minutes)
        
        serializer = self.get_serializer(progress)
        return Response(serializer.data)


class CourseProgressViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CourseProgress tracking.
    
    Users can view and update their own course progress.
    """
    serializer_class = CourseProgressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return course progress for the authenticated user."""
        queryset = CourseProgress.objects.filter(
            user=self.request.user
        ).select_related('course', 'current_lesson')
        
        # Filter by course
        course_id = self.request.query_params.get('course')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        # Filter by completion
        completed = self.request.query_params.get('completed')
        if completed is not None:
            if completed.lower() == 'true':
                queryset = queryset.filter(completed_at__isnull=False)
            else:
                queryset = queryset.filter(completed_at__isnull=True)
        
        return queryset.order_by('-last_accessed')
    
    def perform_create(self, serializer):
        """Set the user when creating progress."""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def advance(self, request, pk=None):
        """
        Move to the next lesson in the course.
        
        POST /api/course-progress/{id}/advance/
        """
        progress = self.get_object()
        next_lesson = progress.advance_to_next_lesson()
        
        if next_lesson:
            from courses.serializers import LessonSerializer
            lesson_serializer = LessonSerializer(next_lesson, context={'request': request})
            return Response({
                'next_lesson': lesson_serializer.data,
                'course_progress': self.get_serializer(progress).data
            })
        else:
            return Response({
                'detail': 'Course completed! No more lessons.',
                'course_progress': self.get_serializer(progress).data
            })
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """
        Get detailed statistics for this course progress.
        
        GET /api/course-progress/{id}/stats/
        """
        progress = self.get_object()
        
        # Get all lesson progress for this course
        lesson_progress_list = LessonProgress.objects.filter(
            user=request.user,
            lesson__module__course=progress.course
        ).select_related('lesson')
        
        # Calculate stats
        total_lessons = progress.course.get_lesson_count()
        completed_lessons = lesson_progress_list.filter(completed=True).count()
        total_time = sum(lp.time_spent_minutes for lp in lesson_progress_list)
        total_attempts = sum(lp.attempts for lp in lesson_progress_list)
        average_score = progress.overall_score
        
        stats = {
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'completion_percentage': progress.get_completion_percentage(),
            'total_time_minutes': total_time,
            'total_time_hours': round(total_time / 60, 2),
            'total_attempts': total_attempts,
            'average_score': average_score,
            'started_at': progress.started_at,
            'completed_at': progress.completed_at,
            'last_accessed': progress.last_accessed,
        }
        
        return Response(stats)
