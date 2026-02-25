# Phase 1 Setup & Usage Guide

## Quick Start

### 1. Admin Panel Access

**Superuser Credentials:**
- Username: `admin`
- Password: Set via: `python3 manage.py changepassword admin`

**Start Server:**
```bash
python3 manage.py runserver
```

**Access Admin:**
http://localhost:8000/admin/

### 2. Create Your First Course

1. Log into admin panel
2. Navigate to **Courses → Courses → Add Course**
3. Fill in:
   - User: select your user
   - Topic: e.g., "Python Programming"
   - Level: Beginner/Intermediate/Advanced
   - Goal: Learning objective
4. Add Modules inline (click "Add another Module")
5. Add Lessons to each Module
6. Save

### 3. Link Resources

1. Go to **Research → Resources → Add Resource**
2. Create a YouTube video or documentation resource
3. Edit your Lesson
4. Link Resources via the M2M field

### 4. Test the System

```bash
# Run verification tests
python3 test_phase1.py

# Expected output: ✅ ALL TESTS PASSED!
```

## Database Schema

**Apps & Models:**
- **courses**: Course, Module, Lesson
- **research**: Resource, ResourceChunk, EmbeddingIndex  
- **progress**: LessonProgress, CourseProgress
- **evaluation**: EvaluationResult, ConceptMastery
- **ai_engine**: LLMPromptLog

## Key Features Implemented

✅ Production-grade models with relationships  
✅ Database indexes for performance  
✅ Unique constraints for data integrity  
✅ Admin panel with hierarchical editing  
✅ Business logic methods (navigation, completion tracking)  
✅ Comprehensive docstrings  

## Next Phase

Ready for **Phase 2: Course Creation API**
- Install Django REST Framework
- Create serializers
- Build API endpoints
- Add authentication

---

**Status:** Phase 1 Complete ✅  
**Tests:** All Passing ✅  
**Admin:** Configured ✅
