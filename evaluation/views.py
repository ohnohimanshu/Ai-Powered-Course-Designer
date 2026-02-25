# evaluation/views.py
"""
API views for the evaluation app.

Provides ViewSets for EvaluationResult and ConceptMastery tracking.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import EvaluationResult, ConceptMastery
from .serializers import EvaluationResultSerializer, ConceptMasterySerializer, QuizSerializer
from .generators import EvaluationGenerator
from courses.models import Lesson


class EvaluationResultViewSet(viewsets.ModelViewSet):
    """
    ViewSet for EvaluationResult management.
    
    Users can create and view their own evaluation results.
    """
    serializer_class = EvaluationResultSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return evaluation results for the authenticated user."""
        queryset = EvaluationResult.objects.filter(
            user=self.request.user
        ).select_related('lesson', 'lesson__module')
        
        # Filter by lesson
        lesson_id = self.request.query_params.get('lesson')
        if lesson_id:
            queryset = queryset.filter(lesson_id=lesson_id)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Set the user when creating an evaluation result."""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def generate_quiz(self, request):
        """
        Generates a new quiz for a lesson.
        POST /api/evaluations/generate_quiz/
        Body: {"lesson_id": 1, "num_questions": 5}
        """
        lesson_id = request.data.get('lesson_id')
        num_questions = int(request.data.get('num_questions', 5))
        
        if not lesson_id:
            return Response({'error': 'lesson_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            lesson = Lesson.objects.get(id=lesson_id)
        except Lesson.DoesNotExist:
            return Response({'error': 'Lesson not found'}, status=status.HTTP_404_NOT_FOUND)
            
        try:
            evaluation = EvaluationGenerator.generate_quiz(request.user, lesson, num_questions)
            # Use QuizSerializer to hide answers
            serializer = QuizSerializer(evaluation)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    @action(detail=True, methods=['post'])
    def submit_quiz(self, request, pk=None):
        """
        Submit answers for a quiz.
        POST /api/evaluations/{id}/submit_quiz/
        Body: {"answers": ["A", "B", ...]}
        """
        evaluation = self.get_object()
        answers = request.data.get('answers')
        
        if not answers or not isinstance(answers, list):
            return Response({'error': 'answers list is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            # Grade
            graded_evaluation = EvaluationGenerator.grade_quiz(evaluation, answers)
            serializer = EvaluationResultSerializer(graded_evaluation)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class ConceptMasteryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ConceptMastery tracking.
    
    Tracks granular mastery levels for individual concepts.
    """
    serializer_class = ConceptMasterySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return concept mastery records for the authenticated user."""
        queryset = ConceptMastery.objects.filter(
            user=self.request.user
        ).select_related('lesson', 'lesson__module')
        
        # Filter by lesson
        lesson_id = self.request.query_params.get('lesson')
        if lesson_id:
            queryset = queryset.filter(lesson_id=lesson_id)
        
        # Filter by concept name (partial match)
        concept = self.request.query_params.get('concept')
        if concept:
            queryset = queryset.filter(concept_name__icontains=concept)
        
        # Filter by mastery level threshold
        min_mastery = self.request.query_params.get('min_mastery')
        if min_mastery:
            try:
                min_mastery_float = float(min_mastery)
                queryset = queryset.filter(mastery_level__gte=min_mastery_float)
            except ValueError:
                pass
        
        return queryset.order_by('-last_practiced')
    
    def perform_create(self, serializer):
        """Set the user when creating a concept mastery record."""
        serializer.save(user=self.request.user)
