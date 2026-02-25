import json
import logging
import re
import requests
import httpx
from django.conf import settings
from functools import lru_cache

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Service for generating vector embeddings from text.
    Uses sentence-transformers locally.
    """
    _model = None

    @classmethod
    def get_model(cls):
        """Singleton pattern to load model only once."""
        if cls._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                model_name = settings.AI_ENGINE['EMBEDDING_MODEL']
                logger.info(f"Loading embedding model: {model_name}")
                cls._model = SentenceTransformer(model_name)
            except ImportError:
                logger.error("sentence-transformers not installed")
                raise
        return cls._model

    @classmethod
    def generate_embedding(cls, text):
        """
        Generate embedding for a string or list of strings.
        Returns: list[float] or list[list[float]]
        """
        model = cls.get_model()
        embeddings = model.encode(text)
        return embeddings.tolist()

    @classmethod
    def chunk_text(cls, text, chunk_size=500, overlap=50):
        """
        Split text into chunks with overlap.
        Simple logic for now, can be improved with recursive splitters.
        """
        if not text:
            return []
            
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i : i + chunk_size])
            chunks.append(chunk)
            if i + chunk_size >= len(words):
                break
        return chunks


class LLMService:
    """
    Service for interacting with LLM (Ollama).
    Supports Synchronous, Async, and Streaming generation.
    """
    BASE_URL = settings.AI_ENGINE['OLLAMA_BASE_URL']
    MODEL = settings.AI_ENGINE['OLLAMA_MODEL']

    @classmethod
    def _clean_json_response(cls, text):
        """
        Attempts to extract valid JSON from LLM response.
        Handles both single objects {} and lists [].
        """
        # Remove markdown code blocks
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```', '', text)
        
        # Find start and end of JSON content
        obj_start = text.find('{')
        list_start = text.find('[')
        
        # Determine if it's likely an object or a list
        if obj_start != -1 and (list_start == -1 or obj_start < list_start):
            start = obj_start
            end = text.rfind('}')
        elif list_start != -1:
            start = list_start
            end = text.rfind(']')
        else:
            return text

        if start != -1 and end != -1:
            text = text[start : end + 1]
            
        # Cleanup common LLM JSON errors
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)
            
        return text

    @classmethod
    def generate_with_retry(cls, prompt, system_prompt=None, temperature=0.7, max_retries=3):
        """
        Synchronous generation with simple retry logic.
        """
        import time
        last_error = None
        for attempt in range(max_retries):
            try:
                return cls.generate(prompt, system_prompt, temperature)
            except Exception as e:
                last_error = e
                logger.warning(f"Ollama attempt {attempt + 1} failed: {e}. Retrying...")
                time.sleep(1 * (attempt + 1)) # Simple backoff
        
        logger.error(f"Ollama failed after {max_retries} attempts.")
        raise last_error

    @classmethod
    async def generate_async_with_retry(cls, prompt, system_prompt=None, temperature=0.7, max_retries=3):
        """
        Async generation with simple retry logic.
        """
        import asyncio
        last_error = None
        for attempt in range(max_retries):
            try:
                return await cls.generate_async(prompt, system_prompt, temperature)
            except Exception as e:
                last_error = e
                logger.warning(f"Ollama async attempt {attempt + 1} failed: {e}. Retrying...")
                await asyncio.sleep(1 * (attempt + 1))
        
        logger.error(f"Ollama async failed after {max_retries} attempts.")
        raise last_error

    @classmethod
    def generate(cls, prompt, system_prompt=None, temperature=0.7):
        """
        Raw synchronous generation call to Ollama.
        """
        url = f"{cls.BASE_URL}/api/generate"
        payload = {
            "model": cls.MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            return response.json().get('response', '')
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama connection failed: {e}")
            raise Exception(f"Failed to connect to AI Engine: {e}")

    @classmethod
    async def generate_async(cls, prompt, system_prompt=None, temperature=0.7):
        """
        Async generation call to Ollama using httpx.
        """
        url = f"{cls.BASE_URL}/api/generate"
        payload = {
            "model": cls.MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json().get('response', '')
        except httpx.RequestError as e:
            logger.error(f"Ollama async connection failed: {e}")
            raise Exception(f"Failed to connect to AI Engine (Async): {e}")

    @classmethod
    async def generate_stream(cls, prompt, system_prompt=None, temperature=0.7, max_retries=3):
        """
        Async streaming generation. Yields text chunks.
        Includes retry logic for initial connection.
        """
        import asyncio
        url = f"{cls.BASE_URL}/api/generate"
        payload = {
            "model": cls.MODEL,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        last_error = None
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    async with client.stream("POST", url, json=payload) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if line:
                                try:
                                    json_response = json.loads(line)
                                    token = json_response.get('response', '')
                                    if token:
                                        yield token
                                    if json_response.get('done', False):
                                        break
                                except json.JSONDecodeError:
                                    continue
                        return # Success, exit retry loop
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                last_error = e
                logger.warning(f"Ollama async stream attempt {attempt + 1} failed: {e}. Retrying...")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))
        
        logger.error(f"Ollama async streaming failed after {max_retries} attempts: {last_error}")
        yield f"[Error: Connection to AI Engine failed - {str(last_error)}]"

    @classmethod
    async def generate_course_structure_async(cls, topic, level, goal):
        """
        Async version of generate_course_structure.
        """
        system_prompt = (
            "You are an expert curriculum designer. "
            "Output strictly valid JSON. No markdown. No conversational text."
        )
        
        prompt = f"""
        Create a detailed course structure for:
        Topic: {topic}
        Level: {level}
        Goal: {goal}
        
        Return a JSON object with this EXACT structure:
        {{
            "title": "Course Title",
            "description": "Course description",
            "modules": [
                {{
                    "title": "Module Title",
                    "description": "Module description",
                    "lessons": [
                        {{
                            "title": "Lesson Title",
                            "description": "What this lesson covers",
                            "type": "text"
                        }}
                    ]
                }}
            ]
        }}
        
        Create at least 3 modules with 2-3 lessons each.
        """
        
        response_text = await cls.generate_async_with_retry(prompt, system_prompt, temperature=0.3)
        
        try:
            cleaned_json = cls._clean_json_response(response_text)
            return json.loads(cleaned_json)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from LLM: {response_text}")
            raise Exception("AI generated invalid structure. Please try again.")

    # Keep synchronous methods for backward compatibility if needed, 
    # but we will switch to async in views.
    @classmethod
    def generate_course_structure(cls, topic, level, goal):
        """
        Generates a course structure (Modules/Lessons) in JSON format.
        """
        system_prompt = (
            "You are an expert curriculum designer. "
            "Output strictly valid JSON. No markdown. No conversational text."
        )
        
        prompt = f"""
        Create a detailed course structure for:
        Topic: {topic}
        Level: {level}
        Goal: {goal}
        
        Return a JSON object with this EXACT structure:
        {{
            "title": "Course Title",
            "description": "Course description",
            "modules": [
                {{
                    "title": "Module Title",
                    "description": "Module description",
                    "lessons": [
                        {{
                            "title": "Lesson Title",
                            "description": "What this lesson covers",
                            "type": "text"
                        }}
                    ]
                }}
            ]
        }}
        
        Create at least 3 modules with 2-3 lessons each.
        """
        
        response_text = cls.generate_with_retry(prompt, system_prompt, temperature=0.3)
        
        try:
            cleaned_json = cls._clean_json_response(response_text)
            return json.loads(cleaned_json)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from LLM: {response_text}")
            raise Exception("AI generated invalid structure. Please try again.")

    @classmethod
    def generate_stream_sync(cls, prompt, system_prompt=None, temperature=0.7, max_retries=3):
        """
        Synchronous streaming generation using requests. Yields text chunks.
        Includes retry logic for initial connection.
        """
        import time
        url = f"{cls.BASE_URL}/api/generate"
        payload = {
            "model": cls.MODEL,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        last_error = None
        for attempt in range(max_retries):
            try:
                with requests.post(url, json=payload, stream=True, timeout=120) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            try:
                                json_response = json.loads(line)
                                token = json_response.get('response', '')
                                if token:
                                    yield token
                                if json_response.get('done', False):
                                    break
                            except json.JSONDecodeError:
                                continue
                    return # Success, exit retry loop
            except requests.exceptions.RequestException as e:
                last_error = e
                logger.warning(f"Ollama stream sync attempt {attempt + 1} failed: {e}. Retrying...")
                if attempt < max_retries - 1:
                    time.sleep(1 * (attempt + 1))

        logger.error(f"Ollama streaming failed after {max_retries} attempts: {last_error}")
        yield f"[Error: Connection to AI Engine failed - {str(last_error)}]"

    @classmethod
    def generate_lesson_content(cls, lesson_title, module_title, context=""):
        """
        Generates content for a specific lesson using RAG context.
        """
        system_prompt = "You are an expert teacher. Write clear, engaging, educational content."
        prompt = cls._build_lesson_prompt(lesson_title, module_title, context)
        return cls.generate_with_retry(prompt, system_prompt, temperature=0.7)

    @classmethod
    def generate_lesson_content_stream(cls, lesson_title, module_title, context=""):
        """
        Generates content for a specific lesson using RAG context (Streaming).
        """
        system_prompt = "You are an expert teacher. Write clear, engaging, educational content."
        prompt = cls._build_lesson_prompt(lesson_title, module_title, context)
        return cls.generate_stream_sync(prompt, system_prompt, temperature=0.7)

    @classmethod
    def _build_lesson_prompt(cls, lesson_title, module_title, context=""):
        """Helper to build a consistent lesson prompt."""
        # Limit context size to avoid blowing up the LLM context window
        if context and len(context) > 10000:
            context = context[:10000] + "... [context truncated for length]"
            
        return f"""
        Write a comprehensive lesson on: "{lesson_title}"
        Part of module: "{module_title}"
        
        Use the following context to inform your content (if relevant):
        {context}
        
        Format using Markdown:
        - Use ## for main sections
        - Use bullet points for key concepts
        - Include a "Summary" at the end
        - Include 1-2 "Practice Questions"
        """

    @classmethod
    def generate_quiz_questions(cls, context, num_questions=5):
        """
        Generates multiple-choice questions based on the provided context.
        Returns a list of dictionaries.
        """
        system_prompt = (
            "You are an expert examiner. "
            "Create multiple-choice questions based on the text provided. "
            "Output strictly valid JSON. "
            "The output MUST be a JSON LIST of objects."
        )
        
        prompt = f"""
        Context:
        {context}
        
        Generate {num_questions} multiple-choice questions based on the above context.
        
        Return a JSON LIST of objects with this EXACT structure:
        [
            {{
                "text": "Question text here?",
                "type": "single_choice",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer": "Option A",
                "explanation": "Why Option A is correct."
            }}
        ]
        
        CRITICAL RULES:
        1. "options" MUST be a list of 4 strings.
        2. "correct_answer" MUST be the exact string from the "options" list.
        3. Output ONLY the JSON list.
        """
        
        response_text = cls.generate_with_retry(prompt, system_prompt, temperature=0.5)
        
        try:
            cleaned_json = cls._clean_json_response(response_text)
            data = json.loads(cleaned_json)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'questions' in data:
                return data['questions']
            return []
        except json.JSONDecodeError:
            logger.error(f"Failed to parse Quiz JSON: {response_text}")
            return []
