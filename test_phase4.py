#!/usr/bin/env python3
"""
Test suite for Phase 4: Assessment & Evaluation
"""
import os
import sys
import json
import django
from unittest.mock import patch, MagicMock

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coursebuilder.settings')
django.setup()

from unittest.mock import MagicMock
# Mock heavy dependencies
try:
    import sentence_transformers
except ImportError:
    sys.modules['sentence_transformers'] = MagicMock()

try:
    import faiss
except ImportError:
    sys.modules['faiss'] = MagicMock()

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from evaluation.generators import EvaluationGenerator
from evaluation.models import EvaluationResult, ConceptMastery
from courses.models import Course, Module, Lesson

class QuizGeneratorTest(TestCase):
    """Test Quiz Generation and Grading"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='quizuser', password='password')
        self.course = Course.objects.create(user=self.user, topic="Test Course")
        self.module = Module.objects.create(course=self.course, title="Module 1", order=0)
        self.lesson = Lesson.objects.create(
            module=self.module, 
            title="Lesson 1", 
            order=0,
            content="This is a lesson about Testing."
        )

    @patch('ai_engine.services.LLMService.generate_quiz_questions')
    def test_generate_quiz(self, mock_generate):
        """Test quiz generation logic"""
        mock_questions = [
            {
                "text": "What is this lesson about?",
                "type": "single_choice",
                "options": ["Testing", "Cooking"],
                "correct_answer": "Testing",
                "explanation": "It says so."
            }
        ]
        mock_generate.return_value = mock_questions
        
        evaluation = EvaluationGenerator.generate_quiz(self.user, self.lesson, num_questions=1)
        
        self.assertEqual(evaluation.user, self.user)
        self.assertEqual(evaluation.lesson, self.lesson)
        self.assertEqual(len(evaluation.questions), 1)
        self.assertEqual(evaluation.questions[0]['correct_answer'], "Testing")
        self.assertEqual(evaluation.score, 0.0)

    def test_grade_quiz(self):
        """Test grading logic"""
        questions = [
            {
                "text": "Q1",
                "correct_answer": "A",
                "explanation": "Exp 1"
            },
            {
                "text": "Q2", 
                "correct_answer": "B",
                "explanation": "Exp 2"
            }
        ]
        
        evaluation = EvaluationResult.objects.create(
            user=self.user,
            lesson=self.lesson,
            questions=questions,
            answers=[],
            score=0.0
        )
        
        # User answers: Correct, Incorrect
        user_answers = ["A", "C"]
        
        graded = EvaluationGenerator.grade_quiz(evaluation, user_answers)
        
        self.assertEqual(graded.score, 50.0)
        self.assertEqual(graded.answers, user_answers)
        self.assertTrue(graded.feedback[0]['correct'])
        self.assertFalse(graded.feedback[1]['correct'])
        
        # Verify Concept Mastery update
        mastery = ConceptMastery.objects.get(user=self.user, lesson=self.lesson)
        self.assertEqual(mastery.attempts, 1)
        # 50% = 0.5 mastery (initial was 0.0, alpha=0.3 -> 0.3*0.5 + 0.7*0.0 = 0.15)
        self.assertAlmostEqual(mastery.mastery_level, 0.15)

class EvaluationAPITest(TestCase):
    """Test Evaluation API Endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='apiuser', password='password')
        self.client.force_authenticate(user=self.user)
        
        self.course = Course.objects.create(user=self.user, topic="Test Course")
        self.module = Module.objects.create(course=self.course, title="Module 1", order=0)
        self.lesson = Lesson.objects.create(
            module=self.module, 
            title="Lesson 1", 
            order=0,
            content="Content"
        )

    @patch('evaluation.generators.EvaluationGenerator.generate_quiz')
    def test_generate_quiz_endpoint(self, mock_gen):
        """Test POST /generate_quiz"""
        mock_eval = EvaluationResult.objects.create(
            user=self.user,
            lesson=self.lesson,
            questions=[{"text": "Q1", "correct_answer": "A", "options": ["A", "B"], "type": "single_choice"}],
            answers=[],
            score=0
        )
        mock_gen.return_value = mock_eval
        
        data = {"lesson_id": self.lesson.id, "num_questions": 1}
        response = self.client.post('/api/evaluations/generate_quiz/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Check that correct_answer is HIDDEN
        self.assertNotIn('correct_answer', response.data['questions'][0])
        self.assertIn('text', response.data['questions'][0])
        
    def test_submit_quiz_endpoint(self):
        """Test POST /submit_quiz"""
        evaluation = EvaluationResult.objects.create(
            user=self.user,
            lesson=self.lesson,
            questions=[{"text": "Q1", "correct_answer": "A"}],
            answers=[],
            score=0
        )
        
        data = {"answers": ["A"]}
        response = self.client.post(f'/api/evaluations/{evaluation.id}/submit_quiz/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Helper logs grading... let's verify score in response or DB
        self.assertEqual(response.data['score'], 100.0)
        # DRF Response.data keeps native types, so key is integer 0
        self.assertTrue(response.data['feedback'][0]['correct'])

def run_tests():
    import unittest
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
    run_tests()
