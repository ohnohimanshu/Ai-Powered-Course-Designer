#!/usr/bin/env python3
"""
Test suite for Phase 3: AI Engine & RAG
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
# Mock heavy dependencies if not installed
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

from ai_engine.services import EmbeddingService, LLMService
from research.services import VectorStoreService
from courses.models import Course, Module, Lesson
from courses.generators import CourseGenerator

class AIUtilsTest(TestCase):
    """Test AI utility services"""
    
    def test_clean_json_response(self):
        """Test robust JSON parsing from markdown"""
        # Case 1: Markdown wrapped
        raw = 'Here is the JSON:\n```json\n{"title": "Test"}\n```'
        cleaned = LLMService._clean_json_response(raw)
        self.assertEqual(cleaned.strip(), '{"title": "Test"}')
        
        # Case 2: Plain text with extra noise
        raw = 'Sure! {"title": "Test"} is the answer.'
        cleaned = LLMService._clean_json_response(raw)
        self.assertEqual(cleaned, '{"title": "Test"}')

class EmbeddingTest(TestCase):
    """Test Embedding Service"""
    
    @patch('sentence_transformers.SentenceTransformer')
    def test_generate_embedding(self, mock_model_cls):
        """Test embedding generation logic"""
        # Setup mock
        mock_instance = MagicMock()
        mock_instance.encode.return_value = MagicMock(tolist=lambda: [0.1, 0.2, 0.3])
        
        # Inject mock into singleton
        EmbeddingService._model = mock_instance
        
        emb = EmbeddingService.generate_embedding("Test text")
        self.assertEqual(emb, [0.1, 0.2, 0.3])

class CourseGeneratorTest(TestCase):
    """Test Course Generation Flow"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='aitestuser', password='password')
        
    @patch('ai_engine.services.requests.post')
    @patch('research.services.VectorStoreService.search')
    @patch('research.models.ResourceChunk.objects.filter')
    def test_lesson_generation_with_rag(self, mock_filter, mock_search, mock_post):
        """Test lesson content generation with RAG context and citations"""
        # Setup Course and Lesson
        course = Course.objects.create(user=self.user, topic="Python")
        module = Module.objects.create(course=course, title="Basics", order=0)
        lesson = Lesson.objects.create(module=module, title="Variables", order=0, content="Old content")
        
        # Mock Vector Search
        mock_search.return_value = [1] # IDs
        
        # Mock ResourceChunk retrieval
        mock_chunk = MagicMock()
        mock_chunk.chunk_text = "Variables store data."
        mock_chunk.resource.title = "Python Docs"
        mock_chunk.resource.url = "http://python.org"
        mock_filter.return_value.select_related.return_value = [mock_chunk]
        
        # Mock LLM response
        # generate_stream_sync yields lines.
        # We need to mock response.iter_lines()
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [
            b'{"response": "Lesson content..."}',
            b'{"response": " is here.", "done": true}'
        ]
        mock_post.return_value.__enter__.return_value = mock_response
        mock_post.return_value.__exit__.return_value = None
        
        # Run generator
        # It's a generator, we need to iterate it
        gen = CourseGenerator.generate_lesson_content_stream(lesson)
        content_chunks = list(gen)
        full_content = "".join(content_chunks)
        
        # Verify Context was used (implicitly by verifying references or just execution)
        # Verify Citations
        self.assertIn("## References", full_content)
        self.assertIn("[Python Docs](http://python.org)", full_content)
        
        # Verify Content Saved
        lesson.refresh_from_db()
        self.assertIn("Lesson content...", lesson.content)
        self.assertIn("## References", lesson.content)
        self.assertTrue(lesson.resources.exists())

    @patch('ai_engine.services.requests.post')
    def test_generate_course_structure(self, mock_post):
        """Test end-to-end course generation with mocked LLM"""
        # ... existing ...
        mock_response = {
            "response": json.dumps({
                "title": "Python Course",
                "description": "Learn Python",
                "modules": [
                    {
                        "title": "Basics",
                        "description": "Intro",
                        "lessons": [{"title": "Variables", "type": "text"}]
                    }
                ]
            })
        }
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.status_code = 200
        
        course = CourseGenerator.generate_course_structure(
            self.user, "Python", "beginner", "Learn basics"
        )
        
        self.assertEqual(course.topic, "Python")
        self.assertEqual(course.modules.count(), 1)
        self.assertEqual(course.modules.first().lessons.count(), 1)
        self.assertEqual(course.modules.first().lessons.first().title, "Variables")

class APIIntegrationTest(TestCase):
    """Test API endpoints for generation"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='apiuser', password='password')
        self.client.force_authenticate(user=self.user)
        
    @patch('courses.generators.CourseGenerator.generate_course_structure')
    def test_generate_endpoint(self, mock_generate):
        """Test POST /api/courses/generate/"""
        # Return a dummy course object
        course = Course.objects.create(user=self.user, topic="Test Gen")
        mock_generate.return_value = course
        
        data = {"topic": "Test Gen", "level": "beginner"}
        response = self.client.post('/api/courses/generate/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['topic'], "Test Gen")

def run_tests():
    import unittest
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
    run_tests()
