# Phase 3 Design Review: RAG & AI Content Generation

## 1. Architectural Review
**Verdict:** **Solid Foundation, but Scalability Risks exist.**
- **Strengths:**
  - **Service-Oriented:** separating `EmbeddingService`, `LLMService`, and `VectorStoreService` is the correct approach. It decouples the business logic from the Django views.
  - **Modular:** Keeping `research` (knowledge) separate from `courses` (product) is good domain-driven design.
- **Weaknesses:**
  - **Synchronous Generation in Views:** Calling a local LLM (Ollama) inside a standard Django `POST` view is a **major anti-pattern**. Local LLMs can take 30s-2mins to generate a full course structure. Usage of `requests.post` will block the specialized Django worker thread, potentially timing out the user's browser or the server (Gunicorn/uWSGI) timeout.
  - **Memory Management:** FAISS indexes are stored in memory. If the index grows large, loading it on every request or indefinitely in the Django process memory is risky. For this scale (interview project), it's acceptable, but a Singleton pattern is required to avoid reloading the index on every request.

## 2. Django Best Practices
- **Good:** Use of `serializers` to validate input before passing to the Generator.
- **Good:** Model definitions are clean.
- **Risk:** Storing `ResourceChunk` without a dedicated `Manager` or efficient bulk creation capability could be slow if ingesting large documents.
- **Recommendation:** Implement a custom Django Command (`manage.py ingest_resources`) for processing embeddings so it doesn't hang the web server.

## 3. LLM & RAG Quality
- **Prompt Strategy**:
  - **Phi Model Limitations**: The `phi` model (while great/efficient) is a small model (~2.7B params). It **struggles with strict JSON output**. Asking it to "Return JSON" often results in markdown-wrapped JSON or broken syntax.
  - **Mitigation**: You MUST implement a "Robust Parser" that uses regex to extract JSON from the response text, or use simpler structured prompts (e.g., allow YAML or plain lists).
- **Chunking**:
  - Naive splitting often breaks context.
  - **Recommendation**: Use a "Recursive Character Splitter" (split by paragraph, then newline, then sentence) logic, or just minimal overlap (e.g., 50 token overlap).

## 4. Performance & Reliability
- **Bottlenecks**:
  - **Ollama Latency**: The biggest bottleneck.
  - **Embedding Generation**: CPU-based `sentence-transformers` is relatively fast but can block the event loop.
- **Solutions**:
  - **Async Views**: Since we successfully installed `uvicorn` (often default in newer Django deployments) or simple `gunicorn`, we should theoretically assume synchronous workers.
  - **Background Tasks (Critical)**: Ideally, use Celery. However, setting up Redis+Celery adds complexity.
  - **Alternative**: Use **Django's database-backend-based/threading approach** or simply accept the wait time but provide a "Polling" mechanism. Return a `task_id` immediately, and let the frontend poll `/api/tasks/{id}`.

## 5. Testing Strategy
- **Mocks are Essential**: Do NOT rely on running Ollama for the CI/CD test suite. It will be too slow and flaky.
- **Mock Implementation**: Create a `MockOllamaBackend` that returns pre-canned valid JSON for "Python Course" queries.
- **Failure Tests**: Test what happens when Ollama is down (ConnectionError). The app should handle this gracefully (HTTP 503).

## 6. Resume & Interview Impact "Wow Factors"
- **Streaming Response**: Implementing **StreamingHttpResponse** to stream the LLM tokens to the frontend in real-time (like ChatGPT) is a *huge* plus. It solves the timeout issue and looks incredible.
- **Explainability**: When a lesson is generated, link it back to the `ResourceChunk` IDs that provided the context ("Source: generic_python_docs.pdf"). This "Citation-backed generation" is a very senior-level feature.
- **Hybrid Search**: Combining Keyword Search (Postgres `trigram`) + Vector Search (FAISS) yields better results than vector search alone.

## 7. Final Verdict
**Is it strong enough?** Yes, for a showcase.
**What MUST be fixed?** The **Synchronous HTTP Call** to Ollama.
- *If you stick to synchronous*: You risk timeouts.
- *Better approach*: Make the endpoint async (`async def generate`) OR return a job ID.

### Actionable Improvements Checklist
1.  [ ] **Switch to Async/Job Queue**: Refactor `CourseGenerator` to be runnable in the background or stream usage. (Simplest for now: **Streaming Response**).
2.  [ ] **Robust JSON Parsing**: Add a helper to clean LLM output (strip markdown backticks) before `json.loads`.
3.  [ ] **Singleton Vector Store**: Ensure FAISS index is loaded once at startup, not per request.
4.  [ ] **Citation Tracking**: Modify `CourseGenerator` to save which `ResourceChunks` were used for each Lesson.
