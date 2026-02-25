import logging
import json
from django.db import transaction
from .models import EvaluationResult, ConceptMastery
from courses.models import Lesson
from ai_engine.services import LLMService

logger = logging.getLogger(__name__)

class EvaluationGenerator:
    """
    Handles generation and grading of quizzes/evaluations.
    """
    
    @staticmethod
    def generate_quiz(user, lesson, num_questions=5):
        """
        Generates a quiz for a specific lesson.
        Creates an EvaluationResult with the questions.
        """
        logger.info(f"Generating quiz for lesson: {lesson.title}")
        
        # 1. Get Context (Lesson Content)
        context = lesson.content
        if not context or len(context) < 100:
            # Fallback to description or resources if content is empty
            context = f"{lesson.title}\n{lesson.description}"
            
        # 2. Generate Questions via LLM
        questions = LLMService.generate_quiz_questions(context, num_questions)
        
        # 3. Validate and Clean Questions
        valid_questions = []
        for q in questions:
            if all(k in q for k in ('text', 'options', 'correct_answer')):
                # Ensure options is a list
                if isinstance(q['options'], list) and len(q['options']) >= 2:
                    valid_questions.append(q)
        
        if not valid_questions:
            logger.error(f"AI generated 0 valid questions for lesson {lesson.id}")
            raise Exception("AI failed to generate valid quiz questions. Please try again.")

        # 4. Create EvaluationResult
        # Store questions but no answers yet
        evaluation = EvaluationResult.objects.create(
            user=user,
            lesson=lesson,
            questions=valid_questions,
            answers=[], # Empty initially
            score=0.0
        )
        
        return evaluation

    @staticmethod
    def grade_quiz(evaluation_result, user_answers):
        """
        Grades a submitted quiz.
        Updates EvaluationResult with score, feedback, and answers.
        Updates ConceptMastery.
        
        Args:
            evaluation_result: EvaluationResult object
            user_answers: List of strings (selected options)
        """
        logger.info(f"Grading quiz: {evaluation_result.id}")
        
        questions = evaluation_result.questions
        score = 0
        total = len(questions)
        feedback = {}
        
        # Simple grading logic
        for idx, question in enumerate(questions):
            correct_answer = question.get('correct_answer')
            
            # Get user answer safely
            if idx < len(user_answers):
                user_ans = user_answers[idx]
            else:
                user_ans = None
                
            is_correct = (user_ans == correct_answer)
            if is_correct:
                score += 1
                
            feedback[idx] = {
                "correct": is_correct,
                "correct_answer": correct_answer,
                "explanation": question.get('explanation', '')
            }
            
        final_score = (score / total) * 100 if total > 0 else 0
        
        # Update EvaluationResult
        evaluation_result.answers = user_answers
        evaluation_result.score = final_score
        evaluation_result.feedback = feedback
        evaluation_result.save()
        
        # Update ConceptMastery for the Lesson (Generic)
        EvaluationGenerator._update_mastery(evaluation_result.user, evaluation_result.lesson, final_score)
        
        return evaluation_result

    @staticmethod
    def _update_mastery(user, lesson, score):
        """
        Updates concept mastery based on quiz score.
        """
        # For simplicity, treat the whole lesson as one concept for now
        concept_name = f"Lesson: {lesson.title}"
        mastery, created = ConceptMastery.objects.get_or_create(
            user=user,
            lesson=lesson,
            concept_name=concept_name
        )
        
        # Normalize score 0-100 to 0.0-1.0
        normalized_score = score / 100.0
        mastery.update_mastery(normalized_score)
