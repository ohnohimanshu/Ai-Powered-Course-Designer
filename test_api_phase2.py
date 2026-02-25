#!/usr/bin/env python3
"""
Comprehensive test suite for Phase 2: Course Creation API

Tests all API endpoints, authentication, permissions, and functionality.
Run with: python3 test_api_phase2.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coursebuilder.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import TestCase, Client
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status

from courses.models import Course, Module, Lesson
from research.models import Resource
from progress.models import LessonProgress, CourseProgress
from evaluation.models import EvaluationResult, ConceptMastery


class APIAuthenticationTest(TestCase):
    """Test API authentication"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
    
    def test_token_authentication(self):
        """Test that token authentication works"""
        # Without token - should fail
        response = self.client.get('/api/courses/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # With token - should succeed
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get('/api/courses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_obtain_token(self):
        """Test obtaining auth token via API"""
        response = self.client.post('/api/auth/token/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)


class CourseAPITest(TestCase):
    """Test Course API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='courseuser',
            email='course@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
    
    def test_create_course(self):
        """Test creating a course via API"""
        data = {
            'topic': 'Python Programming',
            'level': 'beginner',
            'goal': 'Learn Python basics',
            'estimated_duration_hours': 40,
            'description': 'A comprehensive Python course'
        }
        response = self.client.post('/api/courses/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['topic'], 'Python Programming')
        self.assertEqual(response.data['user'], self.user.id)
    
    def test_list_courses(self):
        """Test listing courses"""
        # Create test courses
        Course.objects.create(
            user=self.user,
            topic='Python Programming',
            level='beginner',
            goal='Learn Python',
            estimated_duration_hours=40
        )
        Course.objects.create(
            user=self.user,
            topic='Django Framework',
            level='intermediate',
            goal='Build web apps',
            estimated_duration_hours=60
        )
        
        response = self.client.get('/api/courses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_retrieve_course(self):
        """Test retrieving a single course"""
        course = Course.objects.create(
            user=self.user,
            topic='Python Programming',
            level='beginner',
            goal='Learn Python',
            estimated_duration_hours=40
        )
        
        response = self.client.get(f'/api/courses/{course.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['topic'], 'Python Programming')
    
    def test_update_course(self):
        """Test updating a course"""
        course = Course.objects.create(
            user=self.user,
            topic='Python Programming',
            level='beginner',
            goal='Learn Python',
            estimated_duration_hours=40
        )
        
        data = {'description': 'Updated description'}
        response = self.client.patch(f'/api/courses/{course.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Updated description')
    
    def test_delete_course(self):
        """Test deleting a course"""
        course = Course.objects.create(
            user=self.user,
            topic='Python Programming',
            level='beginner',
            goal='Learn Python',
            estimated_duration_hours=40
        )
        
        response = self.client.delete(f'/api/courses/{course.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Course.objects.filter(id=course.id).exists())
    
    def test_permission_other_user_course(self):
        """Test that users cannot access other users' courses"""
        other_course = Course.objects.create(
            user=self.other_user,
            topic='Private Course',
            level='beginner',
            goal='Test',
            estimated_duration_hours=10
        )
        
        # Should not appear in list
        response = self.client.get('/api/courses/')
        self.assertEqual(len(response.data['results']), 0)
        
        # Should not be able to retrieve
        response = self.client.get(f'/api/courses/{other_course.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_start_course(self):
        """Test starting a course"""
        course = Course.objects.create(
            user=self.user,
            topic='Python Programming',
            level='beginner',
            goal='Learn Python',
            estimated_duration_hours=40
        )
        module = Module.objects.create(
            course=course,
            title='Introduction',
            order=1
        )
        lesson = Lesson.objects.create(
            module=module,
            title='Getting Started',
            order=1,
            content='Welcome to Python!'
        )
        
        response = self.client.post(f'/api/courses/{course.id}/start/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.data['current_lesson'])


class ModuleLessonAPITest(TestCase):
    """Test Module and Lesson API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='moduleuser',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.course = Course.objects.create(
            user=self.user,
            topic='Test Course',
            level='beginner',
            goal='Test',
            estimated_duration_hours=10
        )
    
    def test_create_module(self):
        """Test creating a module"""
        data = {
            'course': self.course.id,
            'title': 'Module 1',
            'description': 'First module',
            'order': 1
        }
        response = self.client.post('/api/modules/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Module 1')
    
    def test_create_lesson(self):
        """Test creating a lesson"""
        module = Module.objects.create(
            course=self.course,
            title='Module 1',
            order=1
        )
        
        data = {
            'module': module.id,
            'title': 'Lesson 1',
            'content': 'Lesson content',
            'content_type': 'text',
            'order': 1,
            'estimated_duration_minutes': 30
        }
        response = self.client.post('/api/lessons/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Lesson 1')
    
    def test_lesson_complete(self):
        """Test completing a lesson"""
        module = Module.objects.create(
            course=self.course,
            title='Module 1',
            order=1
        )
        lesson = Lesson.objects.create(
            module=module,
            title='Lesson 1',
            order=1,
            content='Content'
        )
        
        data = {'score': 85}
        response = self.client.post(f'/api/lessons/{lesson.id}/complete/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['completed'])
        self.assertEqual(response.data['score'], 85)


class ProgressAPITest(TestCase):
    """Test Progress API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='progressuser',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.course = Course.objects.create(
            user=self.user,
            topic='Test Course',
            level='beginner',
            goal='Test',
            estimated_duration_hours=10
        )
        self.module = Module.objects.create(
            course=self.course,
            title='Module 1',
            order=1
        )
        self.lesson = Lesson.objects.create(
            module=self.module,
            title='Lesson 1',
            order=1,
            content='Content'
        )
    
    def test_lesson_progress_list(self):
        """Test listing lesson progress"""
        LessonProgress.objects.create(
            user=self.user,
            lesson=self.lesson,
            score=75,
            completed=True
        )
        
        response = self.client.get('/api/lesson-progress/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_course_progress_stats(self):
        """Test course progress statistics"""
        course_progress = CourseProgress.objects.create(
            user=self.user,
            course=self.course,
            current_lesson=self.lesson
        )
        
        response = self.client.get(f'/api/course-progress/{course_progress.id}/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_lessons', response.data)
        self.assertIn('completion_percentage', response.data)


class ResourceAPITest(TestCase):
    """Test Resource API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='resourceuser',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
    
    def test_list_resources(self):
        """Test listing resources (read-only)"""
        Resource.objects.create(
            resource_type='youtube',
            url='https://youtube.com/watch?v=test',
            title='Test Video'
        )
        
        response = self.client.get('/api/resources/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # At least 1 should be present (may have more from other tests)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_resources_read_only(self):
        """Test that regular users cannot create resources"""
        data = {
            'resource_type': 'youtube',
            'url': 'https://youtube.com/watch?v=new',
            'title': 'New Video'
        }
        response = self.client.post('/api/resources/', data)
        # Should fail because resources are read-only
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


def run_tests():
    """Run all tests"""
    import unittest
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(APIAuthenticationTest))
    suite.addTests(loader.loadTestsFromTestCase(CourseAPITest))
    suite.addTests(loader.loadTestsFromTestCase(ModuleLessonAPITest))
    suite.addTests(loader.loadTestsFromTestCase(ProgressAPITest))
    suite.addTests(loader.loadTestsFromTestCase(ResourceAPITest))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("PHASE 2 API TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED!")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(run_tests())
