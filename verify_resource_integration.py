
import os
import django
from unittest.mock import MagicMock, patch

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coursebuilder.settings')
django.setup()

from courses.generators import CourseGenerator
from research.models import Resource
from courses.models import Course

# Mock ResearchOrchestrator to return some dummy resources
def mock_research_topic(topic):
    print(f"Mock researching {topic}...")
    return [
        {
            'title': 'Test Video 1',
            'url': 'http://youtube.com/watch?v=123',
            'type': 'youtube',
            'description': 'A great video'
        },
        {
            'title': 'Test Doc 1',
            'url': 'http://example.com/doc',
            'type': 'documentation',
            'description': 'A great doc'
        }
    ]

# Mock LLMService to avoid actual LLM calls
class MockLLMService:
    @staticmethod
    def generate_course_structure(topic, level, goal):
        return {
            "title": f"Course on {topic}",
            "description": "Base description.",
            "modules": []
        }

@patch('research.researcher.ResearchOrchestrator.research_topic', side_effect=mock_research_topic)
@patch('courses.generators.LLMService', new=MockLLMService)
def test_resource_integration(mock_research):
    from django.contrib.auth.models import User
    if not User.objects.filter(username='test_user').exists():
        user = User.objects.create_user(username='test_user', password='password')
    else:
        user = User.objects.get(username='test_user')
    
    # Run the generator
    course = CourseGenerator.generate_course_structure(user, "Test Topic", "beginner", "Learn basics")
    
    print(f"Course Description:\n{course.description}")
    
    # Check if resources are in description
    if "Recommended Resources" in course.description:
        print("SUCCESS: Resources found in description.")
        if "Test Video 1" in course.description and "Test Doc 1" in course.description:
             print("SUCCESS: Specific resources found.")
        else:
             print("FAILURE: Specific resources NOT found.")
    else:
        print("FAILURE: Resources section NOT found.")

if __name__ == "__main__":
    test_resource_integration()
