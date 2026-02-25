# API Usage Guide

## Authentication

All API requests (except login) require a token in the header.

**1. Get Token**
```bash
curl -X POST http://localhost:8000/api/auth/token/ \
     -d "username=youruser&password=yourpassword"
```

**Response:**
```json
{"token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"}
```

**2. Make Authenticated Requests**
Header: `Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b`

## Core Workflows

### 1. Course Management

**List Courses:**
`GET /api/courses/`

**Create Course:**
`POST /api/courses/`
```json
{
    "topic": "Advanced Python",
    "level": "intermediate",
    "goal": "Master decorators and generators"
}
```

**Get Next Lesson:**
`GET /api/courses/{id}/next-lesson/`

### 2. Learning Progress

**Mark Lesson Complete:**
`POST /api/lessons/{id}/complete/`
```json
{
    "score": 85
}
```

**Check Course Progress:**
`GET /api/courses/{id}/progress/`

### 3. AI Course Generation (Phase 3)

**Generate Course Structure:**
`POST /api/courses/generate/`
```json
{
    "topic": "Machine Learning",
    "level": "beginner",
    "goal": "Understand Neural Networks"
}
```
*Note: This might take 10-30 seconds depending on local LLM speed.*

**Generate Lesson Content:**
`POST /api/lessons/{id}/generate_content/`
Response:
```json
{
    "content": "# Lesson Title\n\n## Introduction..."
}
```

### 4. Resources


**Search Resources:**
`GET /api/resources/?search=python`

## Error Codes

- `200/201`: Success
- `400`: Validation Error (check response body)
- `401`: Unauthorized (missing/invalid token)
- `403`: Forbidden (accessing another user's data)
- `404`: Not Found
