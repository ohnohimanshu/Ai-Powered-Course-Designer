# progress/models.py
"""
Models for tracking learner progress through courses and lessons.

This app handles:
- Individual lesson completion tracking
- Overall course progress
- Time spent and engagement metrics
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from courses.models import Lesson, Course


class LessonProgress(models.Model):
    """
    Tracks a user's progress through an individual lesson.
    
    Stores completion status, scores, time spent, and detailed
    engagement metrics for adaptive learning.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='lesson_progress',
        help_text="Learner"
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='progress_records',
        help_text="The lesson being tracked"
    )
    score = models.FloatField(
        default=0.0,
        help_text="Latest evaluation score (0-100)"
    )
    completed = models.BooleanField(
        default=False,
        help_text="Whether the lesson has been marked as completed"
    )
    attempts = models.IntegerField(
        default=0,
        help_text="Number of evaluation attempts"
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the user first started this lesson"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the user completed this lesson"
    )
    last_accessed = models.DateTimeField(
        auto_now=True,
        help_text="Last time the user accessed this lesson"
    )
    time_spent_minutes = models.IntegerField(
        default=0,
        help_text="Total time spent on this lesson (in minutes)"
    )
    review_count = models.IntegerField(
        default=0,
        help_text="Number of times the lesson was reviewed after completion"
    )
    metadata = models.JSONField(
        default=dict,
        help_text="Additional tracking data (engagement, difficulty ratings, etc.)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['user', 'lesson']]
        indexes = [
            models.Index(fields=['user', 'lesson', 'completed']),
            models.Index(fields=['user', 'completed']),
            models.Index(fields=['lesson']),
        ]
        verbose_name = "Lesson Progress"
        verbose_name_plural = "Lesson Progress"

    def __str__(self):
        status = "Completed" if self.completed else f"{self.score:.0f}% - In Progress"
        return f"{self.user.username} - {self.lesson.title}: {status}"
    
    def mark_started(self):
        """Mark the lesson as started if not already started."""
        if not self.started_at:
            self.started_at = timezone.now()
            self.save()
    
    def mark_completed(self, score=None):
        """
        Mark the lesson as completed.
        
        Args:
            score: Optional final score (if None, uses current score)
        """
        self.completed = True
        self.completed_at = timezone.now()
        if score is not None:
            self.score = score
        self.save()
    
    def update_time_spent(self, minutes):
        """
        Add time to the total time spent.
        
        Args:
            minutes: Number of minutes to add
        """
        self.time_spent_minutes += minutes
        self.save()
    
    def increment_attempts(self):
        """Increment the evaluation attempts counter."""
        self.attempts += 1
        self.save()


class CourseProgress(models.Model):
    """
    Tracks overall progress through an entire course.
    
    Provides a high-level view of course completion and maintains
    the current position in the course.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='course_progress',
        help_text="Learner"
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='progress_records',
        help_text="The course being tracked"
    )
    current_lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_for_users',
        help_text="The lesson the user is currently working on"
    )
    started_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the user started this course"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the user completed this course"
    )
    overall_score = models.FloatField(
        default=0.0,
        help_text="Average score across all completed lessons"
    )
    metadata = models.JSONField(
        default=dict,
        help_text="Additional course-level metadata (pace, strengths, weaknesses)"
    )
    last_accessed = models.DateTimeField(
        auto_now=True,
        help_text="Last time the user accessed any lesson in this course"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['user', 'course']]
        indexes = [
            models.Index(fields=['user', 'course']),
            models.Index(fields=['user', 'completed_at']),
        ]
        verbose_name = "Course Progress"
        verbose_name_plural = "Course Progress"

    def __str__(self):
        status = "Completed" if self.completed_at else "In Progress"
        return f"{self.user.username} - {self.course.topic}: {status}"
    
    def get_completion_percentage(self):
        """Calculate percentage of lessons completed in this course."""
        return self.course.get_progress_percentage(self.user)
    
    def update_overall_score(self):
        """
        Recalculate the overall course score based on all lesson scores.
        
        Returns the updated score.
        """
        lesson_scores = LessonProgress.objects.filter(
            user=self.user,
            lesson__module__course=self.course,
            completed=True
        ).values_list('score', flat=True)
        
        if lesson_scores:
            self.overall_score = sum(lesson_scores) / len(lesson_scores)
            self.save()
        
        return self.overall_score
    
    def advance_to_next_lesson(self):
        """
        Move to the next lesson in the course sequence.
        
        Returns the new current lesson, or None if course is complete.
        """
        if self.current_lesson:
            next_lesson = self.current_lesson.get_next_lesson()
        else:
            # If no current lesson, start with the first lesson
            first_module = self.course.modules.first()
            next_lesson = first_module.lessons.first() if first_module else None
        
        self.current_lesson = next_lesson
        
        # If no next lesson, mark course as completed
        if not next_lesson and not self.completed_at:
            self.completed_at = timezone.now()
        
        self.save()
        return next_lesson
