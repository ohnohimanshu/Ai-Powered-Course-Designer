import os
import django
import sys
from unittest.mock import MagicMock

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coursebuilder.settings')
django.setup()

from courses.generators import CourseGenerator
from ai_engine.services import LLMService

def verify_fix():
    print("Verifying CourseGenerator argument fix...")
    
    # Mock Lesson and Module
    lesson = MagicMock()
    lesson.title = "Python Decorators"
    lesson.module.title = "Advanced Python"
    lesson.resources.add = MagicMock()
    lesson.save = MagicMock()
    
    # Mock LLMService.generate_lesson_content_stream to avoid actual API call
    # We want to check if it's called with the RIGHT arguments
    original_method = LLMService.generate_lesson_content_stream
    LLMService.generate_lesson_content_stream = MagicMock(return_value=iter(["Chunk 1", "Chunk 2"]))
    
    try:
        # Trigger the generator
        gen = CourseGenerator.generate_lesson_content_stream(lesson)
        chunks = list(gen)
        
        print(f"Generated chunks: {chunks}")
        
        # Check if LLMService.generate_lesson_content_stream was called correctly
        LLMService.generate_lesson_content_stream.assert_called_once()
        args, kwargs = LLMService.generate_lesson_content_stream.call_args
        
        print(f"Called with args: {args}")
        
        if args[0] == lesson.title and args[1] == lesson.module.title:
            print("✅ Arguments are correctly passed (Title and Module Title)!")
        else:
            print(f"❌ Argument mismatch! Expected ({lesson.title}, {lesson.module.title}), got {args}")

    except Exception as e:
        print(f"❌ Error during verification: {e}")
    finally:
        # Restore
        LLMService.generate_lesson_content_stream = original_method

if __name__ == "__main__":
    verify_fix()
