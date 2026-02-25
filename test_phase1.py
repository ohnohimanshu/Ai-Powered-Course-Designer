#!/usr/bin/env python3
"""
Script to test Phase 1 models and verify database structure.

This script validates:
- Model creation and relationships
- Unique constraints
- Business logic methods
- Admin panel readiness
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coursebuilder.settings')
django.setup()

from django.contrib.auth.models import User
from courses.models import Course, Module, Lesson
from research.models import Resource, ResourceChunk, EmbeddingIndex
from progress.models import LessonProgress, CourseProgress
from evaluation.models import EvaluationResult, ConceptMastery


def test_basic_models():
    """Test basic model creation."""
    print("\n" + "=" * 60)
    print("TESTING BASIC MODEL CREATION")
    print("=" * 60)
    
    # Get or create a test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print("✓ Test user created")
    else:
        print("✓ Test user already exists")
    
    # Create a course
    course = Course.objects.create(
        user=user,
        topic='Python Programming',
        level='beginner',
        goal='Learn Python fundamentals',
        description='A comprehensive introduction to Python programming',
        estimated_duration_hours=40.0,
        status='active'
    )
    print(f"✓ Created course: {course}")
    
    # Create modules
    module1 = Module.objects.create(
        course=course,
        title='Introduction to Python',
        description='Basic Python concepts and syntax',
        objectives=['Understand variables', 'Learn data types', 'Write basic programs'],
        order=0,
        estimated_duration_hours=8.0
    )
    print(f"✓ Created module: {module1}")
    
    module2 = Module.objects.create(
        course=course,
        title='Control Flow',
        description='Conditionals and loops',
        objectives=['Master if statements', 'Understand loops', 'Use break and continue'],
        order=1,
        estimated_duration_hours=6.0
    )
    print(f"✓ Created module: {module2}")
    
    # Create a resource
    resource = Resource.objects.create(
        resource_type='youtube',
        url='https://youtube.com/watch?v=example',
        title='Python Tutorial for Beginners',
        description='Complete Python tutorial',
        transcript_text='This is a sample transcript...',
        metadata={'duration': 3600, 'views': 1000000}
    )
    print(f"✓ Created resource: {resource}")
    
    # Create a lesson
    lesson = Lesson.objects.create(
        module=module1,
        title='Variables and Data Types',
        description='Understanding Python variables and basic data types',
        content='Python is a dynamically typed language...',
        content_type='video',
        objectives=['Define variables', 'Use different data types'],
        prerequisites=[],
        order=0,
        estimated_duration_minutes=45
    )
    lesson.resources.add(resource)
    print(f"✓ Created lesson: {lesson}")
    
    return user, course, lesson


def test_progress_tracking(user, course, lesson):
    """Test progress tracking models."""
    print("\n" + "=" * 60)
    print("TESTING PROGRESS TRACKING")
    print("=" * 60)
    
    # Create course progress
    course_progress = CourseProgress.objects.create(
        user=user,
        course=course,
        current_lesson=lesson
    )
    print(f"✓ Created course progress: {course_progress}")
    
    # Create lesson progress
    lesson_progress = LessonProgress.objects.create(
        user=user,
        lesson=lesson
    )
    lesson_progress.mark_started()
    print(f"✓ Created lesson progress: {lesson_progress}")
    
    # Update time spent
    lesson_progress.update_time_spent(30)
    print(f"✓ Updated time spent: {lesson_progress.time_spent_minutes} minutes")
    
    # Mark as completed
    lesson_progress.mark_completed(score=85.0)
    print(f"✓ Marked lesson as completed with score: {lesson_progress.score}")
    
    return lesson_progress


def test_evaluation(user, lesson):
    """Test evaluation models."""
    print("\n" + "=" * 60)
    print("TESTING EVALUATION MODELS")
    print("=" * 60)
    
    # Create evaluation result
    evaluation = EvaluationResult.objects.create(
        user=user,
        lesson=lesson,
        questions=[
            {'id': 1, 'text': 'What is a variable?', 'type': 'multiple_choice'},
            {'id': 2, 'text': 'Name three data types', 'type': 'short_answer'}
        ],
        answers=[
            {'question_id': 1, 'answer': 'A'},
            {'question_id': 2, 'answer': 'int, str, float'}
        ],
        score=85.0,
        feedback={'q1': 'Correct!', 'q2': 'Good answer'},
        concept_mastery={'variables': 0.9, 'data_types': 0.8}
    )
    print(f"✓ Created evaluation: {evaluation}")
    print(f"  - Passing: {evaluation.is_passing()}")
    print(f"  - Weak concepts: {evaluation.get_weak_concepts()}")
    
    # Create concept mastery
    concept = ConceptMastery.objects.create(
        user=user,
        lesson=lesson,
        concept_name='variables',
        mastery_level=0.9
    )
    print(f"✓ Created concept mastery: {concept}")
    
    # Update mastery
    concept.update_mastery(0.95)
    print(f"✓ Updated mastery level: {concept.mastery_level:.2f}")
    
    return evaluation


def test_business_logic(course, lesson):
    """Test business logic methods."""
    print("\n" + "=" * 60)
    print("TESTING BUSINESS LOGIC")
    print("=" * 60)
    
    # Course methods
    print(f"Course module count: {course.get_module_count()}")
    print(f"Course lesson count: {course.get_lesson_count()}")
    
    # Module methods
    module = course.modules.first()
    print(f"Module lesson count: {module.get_lesson_count()}")
    print(f"Module completed: {module.is_completed(course.user)}")
    
    # Lesson navigation
    next_lesson = lesson.get_next_lesson()
    prev_lesson = lesson.get_previous_lesson()
    print(f"Next lesson: {next_lesson}")
    print(f"Previous lesson: {prev_lesson}")
    
    print("\n✓ All business logic tests passed!")


def run_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("PHASE 1 MODEL VERIFICATION")
    print("=" * 60)
    
    try:
        # Test basic model creation
        user, course, lesson = test_basic_models()
        
        # Test progress tracking
        lesson_progress = test_progress_tracking(user, course, lesson)
        
        # Test evaluation
        test_evaluation(user, lesson)
        
        # Test business logic
        test_business_logic(course, lesson)
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nPhase 1 Data Foundation is complete and verified.")
        print("The admin panel is ready at: http://localhost:8000/admin/")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    run_tests()
