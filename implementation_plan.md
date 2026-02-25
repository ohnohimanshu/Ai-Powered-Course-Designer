# Phase 3: RAG & AI Content Generation

Implement the "Brain" of the Course Builder using Vector Search (RAG) and LLM-based content generation.

## User Review Required

> [!IMPORTANT]
> **Dependencies**
> This phase requires installing:
> - `faiss-cpu`: For high-performance vector search
> - `sentence-transformers`: For local embedding generation
> - `requests`: To communicate with local Ollama instance
> 
> **System Requirement**: You must have [Ollama](https://ollama.com/) installed and running with the `phi` model:
> ```bash
> ollama run phi
> ```

> [!NOTE]
> **Performance**
> Using local LLMs is free but depends on your hardware. We'll set reasonable timeouts and fallbacks.

## Proposed Changes

### Setup & Configuration

#### [MODIFY] [settings.py](file:///home/himanshu/coursebuilder/coursebuilder/settings.py)
- Add `ai_engine` configuration:
  - `LLM_PROVIDER = 'ollama'`
  - `OLLAMA_BASE_URL = 'http://localhost:11434'`
  - `OLLAMA_MODEL = 'phi'`

### AI Engine App

#### [NEW] [services.py](file:///home/himanshu/coursebuilder/ai_engine/services.py)
**EmbeddingService**
- `generate_embedding(text)`: Returns list of floats using `all-MiniLM-L6-v2`
- `chunk_text(text, chunk_size)`: Smart text splitting

**LLMService**
- `OllamaBackend`: Connects to local Ollama API
- `generate_course_structure(topic, level)`: Prompts Phi to return JSON
- `generate_lesson_content(topic, context)`: Prompts Phi for content


### Research App

#### [NEW] [services.py](file:///home/himanshu/coursebuilder/research/services.py)
**VectorStoreService**
- `add_chunks(chunks)`: Adds text chunks to FAISS index
- `search(query, k=5)`: Returns relevant `ResourceChunk` objects
- `save_index() / load_index()`: Persistence

#### [MODIFY] [models.py](file:///home/himanshu/coursebuilder/research/models.py)
- Update `ResourceChunk` to maybe store embedding bytes (optional, or just rely on FAISS)

### Courses App

#### [MODIFY] [views.py](file:///home/himanshu/coursebuilder/courses/views.py)
- Add `CourseViewSet.generate` action
- POST `/api/courses/generate/`
    - Body: `{"topic": "...", "level": "..."}`
    - Returns: Created Course object with Modules and Lessons

#### [NEW] [generators.py](file:///home/himanshu/coursebuilder/courses/generators.py)
**CourseGenerator**
- Orchestrates the flow:
  1. Receive topic
  2. (Optional) RAG Search for context
  3. Call LLM to get structure
  4. Create Course/Module/Lesson objects
  5. Return result

## Verification Plan

### Automated Tests
- Test embedding generation (shape check)
- Test standard FAISS operations (add/search)
- Test Course Generation flow (using Mock LLM)

### Manual Verification
- Generate a course via API
- Verify standard structure (Modules/Lessons created)
- Verify search returns relevant chunks
