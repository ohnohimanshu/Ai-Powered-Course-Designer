# courses/models.py
"""
Core domain models for course structure and curriculum.

This app defines the hierarchical structure:
Course → Module → Lesson

Business logic for curriculum design lives here.
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Course(models.Model):
    """
    Represents a complete learning course on a specific topic.
    
    A course is generated based on user's learning intent (topic, level, goal)
    and contains modules which contain lessons.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]
    
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='courses',
        help_text="Learner who requested this course"
    )
    topic = models.CharField(
        max_length=200,
        help_text="Main topic or subject area"
    )
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        help_text="Difficulty level"
    )
    goal = models.TextField(
        help_text="Learning objective or goal stated by the user"
    )
    description = models.TextField(
        blank=True,
        help_text="AI-generated course description"
    )
    estimated_duration_hours = models.FloatField(
        null=True,
        blank=True,
        help_text="Estimated time to complete (in hours)"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        help_text="Current status of the course"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status', 'created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.topic} ({self.get_level_display()}) - {self.user.username}"
    
    def get_module_count(self):
        """Returns total number of modules in this course."""
        return self.modules.count()
    
    def get_lesson_count(self):
        """Returns total number of lessons across all modules."""
        return sum(module.lessons.count() for module in self.modules.all())
    
    def get_progress_percentage(self, user):
        """
        Calculate completion percentage for a user.
        
        Args:
            user: User instance
            
        Returns:
            float: Percentage of lessons completed (0-100)
        """
        from progress.models import LessonProgress
        
        total_lessons = self.get_lesson_count()
        if total_lessons == 0:
            return 0.0
        
        completed_lessons = LessonProgress.objects.filter(
            user=user,
            lesson__module__course=self,
            completed=True
        ).count()
        
        return (completed_lessons / total_lessons) * 100


class Module(models.Model):
    """
    Represents a module (major section) within a course.
    
    Each module focuses on a specific subtopic or skill area
    and contains multiple lessons.
    """
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='modules',
        help_text="Parent course"
    )
    title = models.CharField(
        max_length=300,
        help_text="Module title"
    )
    description = models.TextField(
        blank=True,
        help_text="What this module covers"
    )
    objectives = models.JSONField(
        default=list,
        help_text="Learning objectives for this module (list of strings)"
    )
    order = models.IntegerField(
        help_text="Sequential order within the course (0-based)"
    )
    estimated_duration_hours = models.FloatField(
        null=True,
        blank=True,
        help_text="Estimated time to complete this module"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        unique_together = [['course', 'order']]
        indexes = [
            models.Index(fields=['course', 'order']),
        ]

    def __str__(self):
        return f"{self.course.topic} - Module {self.order + 1}: {self.title}"
    
    def get_lesson_count(self):
        """Returns number of lessons in this module."""
        return self.lessons.count()
    
    def is_completed(self, user):
        """
        Check if user has completed all lessons in this module.
        
        Args:
            user: User instance
            
        Returns:
            bool: True if all lessons are completed
        """
        from progress.models import LessonProgress
        
        total_lessons = self.lessons.count()
        if total_lessons == 0:
            return False
        
        completed_lessons = LessonProgress.objects.filter(
            user=user,
            lesson__module=self,
            completed=True
        ).count()
        
        return completed_lessons == total_lessons
    
    def get_next_module(self):
        """Returns the next module in sequence, or None if this is the last."""
        return Module.objects.filter(
            course=self.course,
            order__gt=self.order
        ).first()


class Lesson(models.Model):
    """
    Represents an individual lesson within a module.
    
    Lessons are the atomic unit of learning. Each lesson:
    - Teaches specific concepts
    - Has associated resources (videos, docs)
    - Can be evaluated for mastery
    """
    CONTENT_TYPE_CHOICES = [
        ('video', 'Video-based'),
        ('text', 'Text/Reading'),
        ('interactive', 'Interactive/Hands-on'),
        ('mixed', 'Mixed Media'),
    ]
    
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='lessons',
        help_text="Parent module"
    )
    title = models.CharField(
        max_length=300,
        help_text="Lesson title"
    )
    description = models.TextField(
        blank=True,
        help_text="Brief description of what this lesson covers"
    )
    content = models.TextField(
        help_text="Main lesson content (text, explanations, examples)"
    )
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        default='mixed',
        help_text="Primary content delivery method"
    )
    objectives = models.JSONField(
        default=list,
        help_text="Specific learning objectives (list of strings)"
    )
    prerequisites = models.JSONField(
        default=list,
        help_text="Concepts that should be understood before this lesson"
    )
    order = models.IntegerField(
        help_text="Sequential order within the module (0-based)"
    )
    estimated_duration_minutes = models.IntegerField(
        null=True,
        blank=True,
        help_text="Estimated time to complete (in minutes)"
    )
    
    # Many-to-many relationship with resources
    resources = models.ManyToManyField(
        'research.Resource',
        related_name='lessons',
        blank=True,
        help_text="Associated learning resources"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        unique_together = [['module', 'order']]
        indexes = [
            models.Index(fields=['module', 'order']),
        ]

    def __str__(self):
        return f"{self.module.title} - Lesson {self.order + 1}: {self.title}"
    
    def get_next_lesson(self):
        """
        Returns the next lesson in the course sequence.
        
        Logic:
        1. Try to get next lesson in same module
        2. If last lesson in module, get first lesson of next module
        3. Return None if this is the last lesson in the course
        """
        # Try next lesson in same module
        next_in_module = Lesson.objects.filter(
            module=self.module,
            order__gt=self.order
        ).first()
        
        if next_in_module:
            return next_in_module
        
        # Try first lesson of next module
        next_module = self.module.get_next_module()
        if next_module:
            return next_module.lessons.first()
        
        return None
    
    def get_previous_lesson(self):
        """
        Returns the previous lesson in the course sequence.
        
        Logic:
        1. Try to get previous lesson in same module
        2. If first lesson in module, get last lesson of previous module
        3. Return None if this is the first lesson in the course
        """
        # Try previous lesson in same module
        prev_in_module = Lesson.objects.filter(
            module=self.module,
            order__lt=self.order
        ).order_by('-order').first()
        
        if prev_in_module:
            return prev_in_module
        
        # Try last lesson of previous module
        prev_module = Module.objects.filter(
            course=self.module.course,
            order__lt=self.module.order
        ).order_by('-order').first()
        
        if prev_module:
            return prev_module.lessons.last()
        
        return None
    
    def is_completed(self, user):
        """Check if user has completed this lesson."""
        from progress.models import LessonProgress
        
        try:
            progress = LessonProgress.objects.get(user=user, lesson=self)
            return progress.completed
        except LessonProgress.DoesNotExist:
            return False
