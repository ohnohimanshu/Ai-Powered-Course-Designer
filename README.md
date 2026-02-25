# Course Builder - AI-Powered Content Generation Platform

A full-stack web application that generates personalized learning courses using AI and Retrieval-Augmented Generation (RAG). Users can specify a topic and learning goals, and the platform automatically creates structured courses with modules, lessons, and assessments.

## 🎯 Project Overview

**Course Builder** is an intelligent learning platform that leverages:
- **Local LLM models** (Phi, Mistral) for course generation and content creation
- **RAG (Retrieval-Augmented Generation)** for grounding course content in researched materials
- **Vector embeddings** and FAISS for semantic search across learning resources
- **Adaptive learning** through progress tracking and concept mastery assessment

The platform enables educators and learners to rapidly create comprehensive educational courses tailored to specific learning objectives and difficulty levels.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (React/TypeScript)           │
│  Dashboard | Course Generation | Lesson Player | Auth   │
└──────────────────┬──────────────────────────────────────┘
                   │ REST API (Axios)
┌──────────────────▼──────────────────────────────────────┐
│              DJANGO REST API (Backend)                   │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Core Apps:                                         │ │
│  │ - Users: Authentication & user management        │ │
│  │ - Courses: Course/Module/Lesson hierarchy        │ │
│  │ - Research: Resource fetching & management       │ │
│  │ - AI Engine: LLM & embedding services            │ │
│  │ - Evaluation: Assessments & concept mastery      │ │
│  │ - Progress: Learner progress tracking            │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
    ┌───▼──┐   ┌───▼──┐   ┌──▼────┐
    │ LLM  │   │Vector│   │SQLite │
    │Svc   │   │Store │   │Database│
    │      │   │(FAISS)  │        │
    └─────┘   └─────┘   └────────┘
```

## 🛠️ Tech Stack

### Backend
- **Framework**: Django 3.2.12
- **API**: Django REST Framework
- **Authentication**: Token-based authentication
- **Database**: SQLite (development)
- **AI/ML**:
  - Local LLM models via HTTP API
  - Sentence-Transformers for embeddings
  - FAISS for vector similarity search
  - Requests/httpx for LLM communication
- **Task Management**: Django ORM with database indexing

### Frontend
- **Framework**: React 19.2.0 with TypeScript
- **Build Tool**: Vite 7.2.4
- **Routing**: React Router 7.13.0
- **Styling**: Tailwind CSS 4.1.18
- **HTTP Client**: Axios 1.13.5
- **Animation**: Framer Motion 12.33.0
- **Icons**: Lucide React 0.563.0
- **Markdown**: React Markdown with syntax highlighting

### Development
- **Linting**: ESLint with TypeScript support
- **Type Checking**: TypeScript 5.9.3
- **CORS**: django-cors-headers

## 📂 Project Structure

```
coursebuilder/
├── coursebuilder/              # Project configuration
│   ├── settings.py            # Django settings
│   ├── urls.py                # URL routing
│   ├── wsgi.py                # WSGI application
│   └── asgi.py                # ASGI application
│
├── users/                      # User management
│   ├── models.py              # User profiles
│   ├── views.py               # Auth endpoints
│   ├── serializers.py         # User serializers
│   └── urls.py                # User routes
│
├── courses/                    # Core course content
│   ├── models.py              # Course/Module/Lesson models
│   ├── views.py               # Course CRUD endpoints
│   ├── generators.py          # AI course generation logic
│   ├── permissions.py         # Access control
│   ├── serializers.py         # Course serializers
│   └── urls.py                # Course routes
│
├── research/                   # Learning resource management
│   ├── models.py              # Resource & ResourceChunk models
│   ├── researcher.py          # Research orchestration
│   ├── services.py            # Vector store operations
│   ├── views.py               # Resource endpoints
│   ├── serializers.py         # Resource serializers
│   └── urls.py                # Research routes
│
├── ai_engine/                  # AI/LLM services
│   ├── models.py              # LLMPromptLog model
│   ├── services.py            # LLM & embedding services
│   ├── views.py               # Status endpoints
│   └── urls.py                # AI routes
│
├── evaluation/                 # Assessment & mastery tracking
│   ├── models.py              # EvaluationResult model
│   ├── generators.py          # Question/assessment generation
│   ├── views.py               # Evaluation endpoints
│   ├── serializers.py         # Evaluation serializers
│   └── urls.py                # Evaluation routes
│
├── progress/                   # Learner progress tracking
│   ├── models.py              # LessonProgress & CourseProgress
│   ├── views.py               # Progress endpoints
│   ├── serializers.py         # Progress serializers
│   └── urls.py                # Progress routes
│
├── frontend/                   # React TypeScript frontend
│   ├── src/
│   │   ├── pages/             # Page components
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── GenerateCourse.tsx
│   │   │   ├── CourseDetail.tsx
│   │   │   └── LessonPlayer.tsx
│   │   ├── components/        # Reusable components
│   │   │   ├── Layout.tsx
│   │   │   ├── CourseCard.tsx
│   │   │   └── ui/
│   │   ├── context/           # React Context (Auth)
│   │   ├── services/          # API client
│   │   ├── utils/             # Utility functions
│   │   ├── App.tsx            # Root component
│   │   └── main.tsx           # Entry point
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── tailwind.config.ts
│
├── manage.py                  # Django CLI
├── db.sqlite3                  # SQLite database
├── test_*.py                   # Test files
└── verify_*.py                 # Verification scripts
```

## 📊 Database Schema

### Core Models

#### **Course**
- Main learning item created by users
- Fields: topic, level, goal, status, description, estimated_duration_hours
- Relations: One-to-many with Module

#### **Module**
- Child of Course; organizational unit
- Fields: title, description, order
- Relations: One-to-many with Lesson

#### **Lesson**
- Building blocks of a course
- Fields: title, description, content, content_type, order
- Relations: Links to evaluations and progress tracking

#### **Resource** & **ResourceChunk**
- Raw learning materials from research
- ResourceChunk: Chunked text for embeddings
- Fields: resource_type, url, transcript_text, token_count

#### **LessonProgress**
- Tracks individual learner progress
- Fields: score, completed, attempts, time_spent_minutes, metadata
- Relations: Many-to-many between User and Lesson

#### **EvaluationResult**
- Assessment results for lessons
- Fields: questions, answers, score, concept_mastery, feedback
- Relations: User + Lesson evaluation data

#### **LLMPromptLog**
- Audit trail for all LLM interactions
- Fields: prompt_type, input_prompt, response, model_name, tokens_used

---

## 🚀 Installation & Setup

### Prerequisites
- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **Git**

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd coursebuilder
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On Linux/Mac
   source venv/bin/activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install django==3.2.12
   pip install djangorestframework
   pip install django-cors-headers
   pip install sentence-transformers
   pip install faiss-cpu
   pip install httpx requests
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start Django development server**
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```
   Frontend will be available at `http://localhost:5173`

4. **Build for production**
   ```bash
   npm run build
   ```

---

## 🎮 Running the Application

### Development Environment

**Terminal 1 - Backend:**
```bash
python manage.py runserver 0.0.0.0:8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Access Points:**
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000/api/`
- Django Admin: `http://localhost:8000/admin/`

### Production Build

```bash
# Frontend
cd frontend
npm run build
# Output in frontend/dist/

# Django (collect static files if needed)
python manage.py collectstatic
```

---

## 📡 API Endpoints Overview

### Authentication
- `POST /api/auth/token/` - Obtain authentication token
- `POST /api/users/register/` - Register new user
- `POST /api/users/login/` - User login

### Courses
- `GET/POST /api/courses/` - List/create courses
- `GET/PUT/DELETE /api/courses/{id}/` - Course detail operations
- `POST /api/courses/{id}/generate/` - Trigger AI course generation
- `GET /api/courses/{id}/modules/` - List course modules
- `GET /api/courses/{id}/lessons/` - List all course lessons

### Lessons
- `GET /api/lessons/{id}/` - Get lesson details
- `PUT /api/lessons/{id}/` - Update lesson content
- `GET /api/lessons/{id}/resources/` - Get related resources

### Research & Resources
- `GET/POST /api/resources/` - List/manage learning resources
- `GET /api/resources/{id}/chunks/` - Get resource chunks
- `POST /api/resources/search/` - Semantic search across resources

### Evaluation
- `POST /api/evaluations/` - Create new evaluation
- `GET /api/evaluations/{id}/` - Get evaluation results
- `POST /api/evaluations/{id}/grade/` - Grade assessment

### Progress
- `GET /api/progress/` - Get user's course progress
- `GET /api/progress/lessons/{id}/` - Get lesson progress
- `PUT /api/progress/lessons/{id}/` - Update lesson progress

### AI Engine
- `GET /api/ai/status/` - Check AI services status
- `POST /api/ai/generate-content/` - Generate lesson content
- `POST /api/ai/generate-questions/` - Generate assessment questions

---

## 🎯 Key Features

### Course Generation
- AI-powered course structure generation from topic and learning goals
- Automatic module and lesson creation
- Integrated research for supplementary resources
- Support for multiple difficulty levels

### Content Creation
- Lesson content generation using local LLM
- RAG-based content grounding in researched materials
- Multiple content types support (text, video, interactive)
- Auto-generated code examples and explanations

### Assessment
- Adaptive question generation based on lesson content
- Automatic scoring and feedback
- Concept-level mastery tracking
- Multiple question types (multiple choice, short answer, etc.)

### Learning Tracking
- Real-time progress monitoring
- Time-spent analytics
- Engagement metrics
- Concept mastery dashboards
- Performance history

### Research & Resources
- Automatic research on course topics
- YouTube video fetching and transcription
- Documentation and article sources
- Vector-based semantic search
- Resource chunking for better retrieval

---

## 🔄 Workflow

### Typical User Journey

1. **User Registration/Login**
   - Authentication via token-based system
   - User profiles created in the system

2. **Course Generation**
   - User specifies: topic, learning level, goals
   - System researches the topic
   - AI generates structured course outline
   - Database populated with Course → Modules → Lessons

3. **Course Review**
   - User views generated course structure
   - Can inspect individual lessons
   - Reviews recommended resources
   - Optional: Edit/refine lessons (future phase)

4. **Active Learning**
   - User opens lesson in lesson player
   - Views AI-generated content
   - Resources and references provided
   - Tracks time spent on lesson

5. **Assessment**
   - System generates adaptive questions
   - User answers evaluation questions
   - AI grades responses
   - Concept mastery scores calculated
   - Feedback provided

6. **Progress Tracking**
   - Dashboard shows completion status
   - Performance analytics visible
   - Weakness in concepts identified
   - Personalized recommendations (future phase)

---

## ⚙️ Configuration

### Django Settings (`coursebuilder/settings.py`)

**Key Settings:**
```python
# AI Engine Configuration
AI_ENGINE = {
    'EMBEDDING_MODEL': 'sentence-transformers/all-MiniLM-L6-v2',
    'VECTOR_STORE_PATH': 'vector_store/',
    'LLM_API_URL': 'http://localhost:11434/api/generate',
    'DEFAULT_MODEL': 'phi',
}

# CORS for frontend
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

### Frontend Configuration (`.env`)
```
VITE_API_URL=http://localhost:8000/api
VITE_DEBUG=true
```

---

## 🧪 Testing

Run test suites for each component:

```bash
# All tests
python manage.py test

# Specific app tests
python manage.py test courses
python manage.py test research
python manage.py test evaluation

# Verification scripts
python verify_fixes.py
python verify_argument_fix.py
python verify_resource_integration.py
```

Test files:
- `test_phase1.py` - Basic API tests
- `test_api_phase2.py` - Course generation tests
- `test_phase3.py` - Assessment tests
- `test_phase4.py` - Integration tests
- `test_json_cleaning.py` - JSON parsing tests
- `test_research_fetching.py` - Research service tests

---

## 📝 Development Guide

### Adding New Features

1. **Create a new app** (if needed)
   ```bash
   python manage.py startapp myfeature
   ```

2. **Define models** in `models.py`

3. **Create serializers** in `serializers.py`

4. **Implement views** in `views.py` using ViewSets

5. **Add URL routing** in `urls.py`

6. **Register in admin** (if needed)

7. **Write tests** in `tests.py`

### Code Organization Principles

- **Models**: Business logic and data structure
- **Serializers**: Request/response formatting
- **Views**: HTTP logic and permissions
- **Services**: Reusable business logic (LLM, embeddings, research)
- **Generators**: Complex orchestration logic
- **Permissions**: Access control

### Frontend Component Structure

```
Component/
├── Component.tsx          # Main component
├── Component.module.css   # Styles
├── Component.types.ts     # TypeScript definitions
└── use*.ts                # Custom hooks
```

---

## 🐛 Troubleshooting

### Backend Issues

**LLM Connection Error**
```
Error: Connection refused at localhost:11434
```
Solution: Ensure LLM service is running (Ollama, LM Studio, etc.)

**CORS Error**
```
Access to XMLHttpRequest blocked by CORS policy
```
Solution: Check `CORS_ALLOWED_ORIGINS` in settings.py

**Vector Store Error**
```
ModuleNotFoundError: No module named 'faiss'
```
Solution: `pip install faiss-cpu`

### Frontend Issues

**API Connection Refused**
Solution: Ensure Django backend is running on port 8000

**Build Errors**
```bash
npm run build
# Check TypeScript errors
npm run lint
```

---

## 📚 Documentation References

- [Django Documentation](https://docs.djangoproject.com/en/3.2/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [React Documentation](https://react.dev/)
- [Vite Guide](https://vitejs.dev/)
- [Sentence Transformers](https://www.sbert.net/)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style
- **Python**: Follow PEP 8, use docstrings
- **JavaScript/TypeScript**: ESLint configuration provided
- Use meaningful variable names
- Add comments for complex logic

---

## 📄 License

This project is provided as-is for educational and commercial use.

---

## 👥 Authors & Contributors

- **Himanshu** - Project Creator

## 📞 Support & Contact

For issues, questions, or suggestions:
1. Check existing GitHub issues
2. Create a new issue with detailed description
3. Contact: [Your Contact Info]

---

## 🗺️ Roadmap

### Phase 1 ✅ (Completed)
- Basic course structure (Course → Module → Lesson)
- User authentication
- Course CRUD operations

### Phase 2 ✅ (Completed)
- AI course generation with LLM
- Research integration
- Vector store for semantic search

### Phase 3 ✅ (Completed)
- Automated assessment generation
- Concept mastery tracking
- Evaluation scoring

### Phase 4 🔄 (In Progress)
- Progress dashboard
- Performance analytics
- Adaptive learning recommendations

### Phase 5 (Planned)
- Mobile app (React Native)
- Advanced analytics
- Team/organization management
- Real-time collaboration
- Completion certificates

---

## 🎓 Learning Resources Generated

Example course structure for "Machine Learning Fundamentals":

```
Course: Machine Learning Fundamentals (Intermediate)
├── Module 1: Introduction to ML
│   ├── Lesson 1: What is Machine Learning?
│   ├── Lesson 2: Types of Learning (Supervised, Unsupervised, RL)
│   └── Lesson 3: ML Workflow & Applications
├── Module 2: Data Preparation
│   ├── Lesson 1: Data Collection & Cleaning
│   ├── Lesson 2: Feature Engineering
│   └── Lesson 3: Data Splitting (Train/Val/Test)
├── Module 3: Supervised Learning
│   ├── Lesson 1: Linear Regression
│   ├── Lesson 2: Logistic Regression
│   ├── Lesson 3: Decision Trees
│   └── Lesson 4: Ensemble Methods (Random Forest)
├── Module 4: Model Evaluation
│   ├── Lesson 1: Metrics (Accuracy, Precision, Recall, F1)
│   ├── Lesson 2: Cross-Validation
│   └── Lesson 3: Hyperparameter Tuning
└── Module 5: Practical Project
    └── Lesson 1: End-to-end ML Project
```

Each lesson includes:
- Generated explanations and examples
- Recommended YouTube tutorials
- Official documentation links
- Assessment questions
- Progress tracking

---

## 🚀 Performance Optimization Tips

1. **Database Queries**: Use `select_related()` and `prefetch_related()`
2. **Caching**: Implement Redis for frequently accessed data
3. **Frontend**: Code splitting with React Router lazy loading
4. **API**: Implement pagination for large datasets
5. **Vector Store**: Batch operations for embedding generation

---

**Last Updated**: February 2026
**Version**: 1.0.0
**Status**: Active Development

