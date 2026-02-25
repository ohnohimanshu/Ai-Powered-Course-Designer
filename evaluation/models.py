# evaluation/models.py
"""
Models for learner evaluation and concept mastery tracking.

This app handles:
- Assessment results and scoring
- Granular concept-level mastery tracking
- Data for adaptive learning decisions
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from courses.models import Lesson


class EvaluationResult(models.Model):
    """
    Stores the result of a lesson evaluation/assessment.
    
    Evaluations test learner understanding through questions generated
    via RAG from the lesson content and resources.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='evaluation_results',
        help_text="Learner being evaluated"
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='evaluation_results',
        help_text="Lesson being evaluated"
    )
    questions = models.JSONField(
        help_text="List of question objects with text, type, and expected answers"
    )
    answers = models.JSONField(
        help_text="User's answers to the questions"
    )
    score = models.FloatField(
        help_text="Overall score for this evaluation (0-100)"
    )
    feedback = models.JSONField(
        default=dict,
        help_text="Question-by-question feedback and explanations"
    )
    concept_mastery = models.JSONField(
        default=dict,
        help_text="Mapping of concept names to mastery levels (0.0-1.0)"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'lesson', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['lesson']),
        ]
        verbose_name = "Evaluation Result"
        verbose_name_plural = "Evaluation Results"

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title}: {self.score:.1f}%"
    
    def is_passing(self, threshold=70.0):
        """
        Check if the evaluation meets the passing threshold.
        
        Args:
            threshold: Minimum score to pass (default 70%)
            
        Returns:
            bool: True if score >= threshold
        """
        return self.score >= threshold
    
    def get_weak_concepts(self, threshold=0.6):
        """
        Identify concepts that need reinforcement.
        
        Args:
            threshold: Minimum mastery level (default 0.6)
            
        Returns:
            list: Names of concepts with mastery below threshold
        """
        return [
            concept
            for concept, mastery in self.concept_mastery.items()
            if mastery < threshold
        ]


class ConceptMastery(models.Model):
    """
    Tracks granular mastery of individual concepts within lessons.
    
    This enables adaptive learning by identifying:
    - Which concepts a learner struggles with
    - How mastery improves over time
    - When to move on vs. reinforce
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='concept_mastery',
        help_text="Learner"
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='concept_mastery',
        help_text="Lesson containing this concept"
    )
    concept_name = models.CharField(
        max_length=200,
        help_text="Name or identifier of the concept"
    )
    mastery_level = models.FloatField(
        default=0.0,
        help_text="Current mastery level (0.0 = no understanding, 1.0 = full mastery)"
    )
    attempts = models.IntegerField(
        default=0,
        help_text="Number of times this concept has been evaluated"
    )
    last_evaluated = models.DateTimeField(
        auto_now=True,
        help_text="Last time this concept was assessed"
    )
    metadata = models.JSONField(
        default=dict,
        help_text="Additional tracking (mistake patterns, improvement rate, etc.)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['user', 'lesson', 'concept_name']]
        indexes = [
            models.Index(fields=['user', 'lesson']),
            models.Index(fields=['user', 'mastery_level']),
        ]
        verbose_name = "Concept Mastery"
        verbose_name_plural = "Concept Mastery"

    def __str__(self):
        return f"{self.user.username} - {self.concept_name}: {self.mastery_level:.0%}"
    
    def update_mastery(self, new_score):
        """
        Update mastery level based on a new evaluation score.
        
        Uses exponential moving average to:
        - Weight recent performance more heavily
        - Maintain historical context
        
        Args:
            new_score: Score from latest evaluation (0.0-1.0)
        """
        # Exponential moving average with alpha=0.3
        # (weights recent performance at 30%, historical at 70%)
        alpha = 0.3
        self.mastery_level = alpha * new_score + (1 - alpha) * self.mastery_level
        self.attempts += 1
        self.save()
    
    def needs_reinforcement(self, threshold=0.7):
        """
        Determine if this concept needs additional practice.
        
        Args:
            threshold: Minimum acceptable mastery level
            
        Returns:
            bool: True if mastery is below threshold
        """
        return self.mastery_level < threshold
