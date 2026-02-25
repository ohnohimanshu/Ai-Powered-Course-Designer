import logging
import json
from django.db import transaction
from courses.models import Course, Module, Lesson
from ai_engine.services import LLMService

logger = logging.getLogger(__name__)

class CourseGenerator:
    """
    Orchestrates the AI course generation process.
    """
    
    @staticmethod
    def generate_course_structure(user, topic, level, goal):
        """
        1. Calls LLM to get course outline.
        2. Creates DB objects (Course, Module, Lesson).
        Returns: Course object
        """
        logger.info(f"Generating course structure for: {topic}")
        
        # 1. Research the topic to populate vector store
        try:
            from research.researcher import ResearchOrchestrator
            ResearchOrchestrator.research_topic(topic)
        except Exception as e:
            logger.error(f"Research failed for {topic}: {e}")
            
        # 2. Get Structure from LLM
        structure = LLMService.generate_course_structure(topic, level, goal)
        
        # 3. Save to DB transactionally
        with transaction.atomic():
            course = Course.objects.create(
                user=user,
                topic=topic,
                level=level,
                goal=goal,
                description=structure.get('description', ''),
                status='draft'
            )
            
            for m_idx, module_data in enumerate(structure.get('modules', [])):
                module = Module.objects.create(
                    course=course,
                    title=module_data.get('title'),
                    description=module_data.get('description', ''),
                    order=m_idx
                )
                
                for l_idx, lesson_data in enumerate(module_data.get('lessons', [])):
                    Lesson.objects.create(
                        module=module,
                        title=lesson_data.get('title'),
                        description=lesson_data.get('description', ''),
                        content_type=lesson_data.get('type', 'text'),
                        order=l_idx,
                        # Initial content is empty or placeholder
                        content="Content not generated yet. Click 'Generate Content' to create."
                    )
            
            logger.info(f"Course created: {course.id}")
            return course

    @staticmethod
    def generate_lesson_content_stream(lesson):
        """
        Generates content for a single lesson using streaming (Sync Generator).
        Yields chunks of text.
        """
        from research.services import VectorStoreService
        from research.models import ResourceChunk

        logger.info(f"Streaming content for lesson: {lesson.title}")
        
        # Retrieve RAG context
        chunk_ids = VectorStoreService.search(lesson.title)
        context = ""
        used_resources = set()

        if chunk_ids:
            chunks = ResourceChunk.objects.filter(id__in=chunk_ids).select_related('resource')
            context_parts = []
            for chunk in chunks:
                context_parts.append(f"Content from '{chunk.resource.title}':\n{chunk.chunk_text}")
                used_resources.add(chunk.resource)
            context = "\n\n".join(context_parts)
            logger.info(f"Found {len(chunks)} chunks for context.")
        
        full_content = []
        # Use sync stream helper
        for chunk in LLMService.generate_lesson_content_stream(
            lesson.title, 
            lesson.module.title, 
            context
        ):
            full_content.append(chunk)
            yield chunk

        # Append citations
        references = ""
        if used_resources:
            # Link resources to lesson
            lesson.resources.add(*used_resources)
            
            references = "\n\n## References\n"
            for res in used_resources:
                 references += f"- [{res.title}]({res.url})\n"
            
            yield references

        # Save the full content to DB at the end
        final_content = "".join(full_content) + references
        lesson.content = final_content
        lesson.save()

    @staticmethod
    def _save_lesson_content(lesson, content):
        lesson.content = content
        lesson.save()
