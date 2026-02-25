import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coursebuilder.settings')
django.setup()

from courses.models import Lesson, Course
from courses.serializers import LessonSerializer
from research.researcher import ResearchOrchestrator
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

def verify_serializer():
    print("Verifying LessonSerializer...")
    try:
        lesson = Lesson.objects.first()
        if not lesson:
            print("No lessons found in DB. Creating one for test.")
            from django.contrib.auth.models import User
            from courses.models import Module
            user = User.objects.first() or User.objects.create(username="testuser")
            course = Course.objects.create(user=user, topic="Test Course")
            module = Module.objects.create(course=course, title="Test Module", order=0)
            lesson = Lesson.objects.create(module=module, title="Test Lesson", order=0, content="Test content")
        
        factory = APIRequestFactory()
        request = factory.get('/')
        serializer_context = {'request': Request(request)}
        
        serializer = LessonSerializer(lesson, context=serializer_context)
        data = serializer.data
        print(f"Serializer data keys: {data.keys()}")
        if 'next_lesson' in data and 'previous_lesson' in data and 'is_completed' in data:
            print("✅ LessonSerializer fix verified!")
        else:
            print("❌ LessonSerializer fix failed! Missing fields.")
    except Exception as e:
        print(f"❌ Error verifying serializer: {e}")

def verify_research():
    print("\nVerifying Research Pipeline...")
    try:
        topic = "Python Decorators"
        ResearchOrchestrator.research_topic(topic)
        
        from research.models import Resource
        resources = Resource.objects.filter(title__icontains=topic)
        if resources.exists():
            print(f"✅ Research pipeline verified! Found {resources.count()} resources.")
            for res in resources:
                print(f" - {res.title} ({res.resource_type})")
        else:
            print("❌ Research pipeline failed! No resources found.")
    except Exception as e:
        print(f"❌ Error verifying research: {e}")

if __name__ == "__main__":
    verify_serializer()
    verify_research()
